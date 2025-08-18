# backend/apps/analytics/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum, Q
from apps.conversations.models import Conversation, Message
from apps.analytics.models import HourlyMetrics, DailyMetrics
from apps.accounts.models import Organization
import logging
from apps.agents.models import Agent

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def aggregate_metrics(self, hours_back=1):
    """Aggregate metrics for the past hour(s)"""
    try:
        end_time = timezone.now().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=hours_back)
        
        logger.info(f"Starting metrics aggregation from {start_time} to {end_time}")
        
        organizations = Organization.objects.filter(is_active=True)
        
        for org in organizations:
            process_organization_metrics.delay(
                org.id, 
                start_time.isoformat(), 
                end_time.isoformat()
            )
        
        return f"Queued metrics aggregation for {organizations.count()} organizations"
    
    except Exception as exc:
        logger.error(f"Metrics aggregation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def process_organization_metrics(self, org_id, start_time_str, end_time_str):
    """Process metrics for a single organization"""
    try:
        org = Organization.objects.get(id=org_id)
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        
        current_hour = start_time
        
        while current_hour < end_time:
            next_hour = current_hour + timedelta(hours=1)
            
            # Get all agents for this org
            agents = Agent.objects.filter(organization=org, is_active=True)
            
            # Organization-wide metrics
            org_conversations = Conversation.objects.filter(
                agent__organization=org,
                started_at__gte=current_hour,
                started_at__lt=next_hour
            )
            
            org_metrics = calculate_metrics_for_queryset(org_conversations, org, current_hour)
            
            # Save organization-level metrics
            HourlyMetrics.objects.update_or_create(
                organization=org,
                agent=None,  # Null means org-wide
                timestamp=current_hour,
                defaults=org_metrics
            )
            
            # Per-agent metrics
            for agent in agents:
                agent_conversations = org_conversations.filter(agent=agent)
                if agent_conversations.exists():
                    agent_metrics = calculate_metrics_for_queryset(
                        agent_conversations, org, current_hour
                    )
                    
                    HourlyMetrics.objects.update_or_create(
                        organization=org,
                        agent=agent,
                        timestamp=current_hour,
                        defaults=agent_metrics
                    )
            
            current_hour = next_hour
        
        logger.info(f"Completed metrics for org {org.name}")
        return f"Processed metrics for {org.name}"
    
    except Exception as exc:
        logger.error(f"Failed to process org {org_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)

def calculate_metrics_for_queryset(conversations, org, timestamp):
    """Calculate metrics for a queryset of conversations"""
    
    # Basic counts
    metrics = {
        'total_conversations': conversations.count(),
        'active_conversations': conversations.filter(status='active').count(),
        'ended_conversations': conversations.filter(status='ended').count(),
        'handed_off_conversations': conversations.filter(status='handed_off').count(),
        'whatsapp_conversations': conversations.filter(channel='whatsapp').count(),
        'sms_conversations': conversations.filter(channel='sms').count(),
        'voice_conversations': conversations.filter(channel='voice').count(),
    }
    
    # Message metrics
    messages = Message.objects.filter(
        conversation__in=conversations,
        created_at__gte=timestamp,
        created_at__lt=timestamp + timedelta(hours=1)
    )
    
    metrics.update({
        'total_messages': messages.count(),
        'ai_messages': messages.filter(sender_type='agent').count(),
        'human_messages': messages.filter(sender_type='human').count(),
        'customer_messages': messages.filter(sender_type='customer').count(),
    })
    
    # Averages
    avg_data = conversations.aggregate(
        avg_response=Avg('first_response_time_seconds'),
        avg_messages=Avg('message_count')
    )
    
    metrics['avg_response_time_seconds'] = avg_data['avg_response'] or 0
    metrics['avg_messages_per_conversation'] = avg_data['avg_messages'] or 0
    
    # Calculate average duration for ended conversations
    ended_convs = conversations.filter(status='ended', ended_at__isnull=False)
    if ended_convs.exists():
        durations = []
        for conv in ended_convs:
            if conv.ended_at and conv.started_at:
                duration = (conv.ended_at - conv.started_at).total_seconds() / 60
                durations.append(duration)
        
        metrics['avg_conversation_duration_minutes'] = (
            sum(durations) / len(durations) if durations else 0
        )
    else:
        metrics['avg_conversation_duration_minutes'] = 0
    
    return metrics

@shared_task
def aggregate_daily_metrics():
    """Aggregate daily metrics from hourly data"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    for org in Organization.objects.filter(is_active=True):
        hourly_data = HourlyMetrics.objects.filter(
            organization=org,
            agent=None,  # Org-wide metrics only
            timestamp__date=yesterday
        ).aggregate(
            total_conversations=Sum('total_conversations'),
            total_messages=Sum('total_messages'),
            whatsapp_conversations=Sum('whatsapp_conversations'),
            sms_conversations=Sum('sms_conversations'),
            voice_conversations=Sum('voice_conversations'),
        )
        
        # Calculate unique customers
        unique_customers = Conversation.objects.filter(
            agent__organization=org,
            started_at__date=yesterday
        ).values('customer_phone').distinct().count()
        
        # Calculate costs (using your pricing model)
        costs = calculate_daily_costs(org, yesterday)
        
        DailyMetrics.objects.update_or_create(
            organization=org,
            date=yesterday,
            defaults={
                'total_conversations': hourly_data['total_conversations'] or 0,
                'total_messages': hourly_data['total_messages'] or 0,
                'unique_customers': unique_customers,
                'total_cost': costs['total'],
                'whatsapp_cost': costs['whatsapp'],
                'sms_cost': costs['sms'],
                'voice_minutes': costs['voice_minutes'],
                'voice_cost': costs['voice'],
            }
        )
    
    logger.info(f"Aggregated daily metrics for {yesterday}")

def calculate_daily_costs(org, date):
    """Calculate costs for a given day based on usage"""
    
    #! TODO: Define your pricing (could move to database/settings)
    PRICING = {
        'whatsapp': 0.005,  # per message
        'sms': 0.01,        # per message
        'voice': 0.02,      # per minute
    }
    
    conversations = Conversation.objects.filter(
        agent__organization=org,
        started_at__date=date
    )
    
    # Calculate message costs
    whatsapp_messages = Message.objects.filter(
        conversation__in=conversations.filter(channel='whatsapp'),
        created_at__date=date,
        sender_type='agent'  # Only count outbound
    ).count()
    
    sms_messages = Message.objects.filter(
        conversation__in=conversations.filter(channel='sms'),
        created_at__date=date,
        sender_type='agent'
    ).count()
    
    # Calculate voice minutes (assuming you track this somewhere)
    voice_conversations = conversations.filter(channel='voice')
    voice_minutes = 0
    for conv in voice_conversations:
        if conv.ended_at and conv.started_at:
            duration_minutes = (conv.ended_at - conv.started_at).total_seconds() / 60
            voice_minutes += duration_minutes
    
    return {
        'whatsapp': whatsapp_messages * PRICING['whatsapp'],
        'sms': sms_messages * PRICING['sms'],
        'voice': voice_minutes * PRICING['voice'],
        'voice_minutes': int(voice_minutes),
        'total': (whatsapp_messages * PRICING['whatsapp'] + 
                 sms_messages * PRICING['sms'] + 
                 voice_minutes * PRICING['voice'])
    }

@shared_task
def cleanup_old_metrics():
    """Clean up old detailed metrics, keep only aggregated data"""
    # Keep hourly metrics for 30 days
    cutoff_hourly = timezone.now() - timedelta(days=30)
    deleted_hourly = HourlyMetrics.objects.filter(
        timestamp__lt=cutoff_hourly
    ).delete()
    
    # Keep daily metrics for 1 year
    cutoff_daily = timezone.now() - timedelta(days=365)
    deleted_daily = DailyMetrics.objects.filter(
        date__lt=cutoff_daily.date()
    ).delete()
    
    logger.info(f"Cleaned up metrics: {deleted_hourly[0]} hourly, {deleted_daily[0]} daily")
    return f"Deleted {deleted_hourly[0]} hourly and {deleted_daily[0]} daily records"