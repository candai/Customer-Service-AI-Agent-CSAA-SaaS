# backend/apps/conversations/analytics.py

import csv
from uuid import UUID
from django.http import HttpResponse
from ninja import Router, Schema
from django.db.models import Count, Avg, Sum, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, TruncHour, TruncWeek, TruncMonth, ExtractHour, ExtractWeekDay
from django.utils import timezone
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from apps.conversations.models import Conversation, Message
from apps.agents.models import Agent
from apps.accounts.api import auth
from ..conversations.schemas import AnalyticsParams, ConversationStatsResponse
from django.db.models import Min, Max
import logging

logger = logging.getLogger(__name__)

router = Router(tags=["Analytics"])

####################################################
###########! Time-Series Export API ###########
####################################################


@router.post("/overview", auth=auth)
def get_analytics_overview(request, params: AnalyticsParams):
    """Get comprehensive analytics overview"""
    
    user = request.auth
    
    # Default date range (last 30 days)
    if not params.date_to:
        params.date_to = timezone.now()
    if not params.date_from:
        params.date_from = params.date_to - timedelta(days=30)
    
    # Base queryset
    queryset = Conversation.objects.filter(
        agent__organization=user.organization,
        started_at__gte=params.date_from,
        started_at__lte=params.date_to
    )
    
    if params.agent_uuid_string:
        agent_id_uuid = UUID(params.agent_uuid_string)
        queryset = queryset.filter(agent_id=agent_id_uuid)
    
    if params.channel:
        queryset = queryset.filter(channel=params.channel)
    
    # Summary statistics
    summary = {
        'total_conversations': queryset.count(),
        'total_messages': Message.objects.filter(
            conversation__in=queryset
        ).count(),
        'avg_messages_per_conversation': queryset.aggregate(
            avg=Avg('message_count')
        )['avg'] or 0,
        'unique_customers': queryset.values('customer_phone').distinct().count(),
        'handoff_rate': (queryset.filter(handed_off_at__isnull=False).count() / 
                        max(queryset.count(), 1)) * 100,
    }
    
    # Conversation trends
    trends = get_conversation_trends(queryset, params.granularity)
    
    # Channel distribution
    channel_distribution = list(queryset.values('channel').annotate(
        count=Count('id'),
        avg_messages=Avg('message_count')
    ).order_by('-count'))
    
    # Agent performance
    agent_performance = get_agent_performance(user.organization, params.date_from, params.date_to)
    
    # Peak hours analysis
    peak_hours = get_peak_hours(queryset)
    
    # Response times
    response_times = get_response_times(queryset)
    
    # Customer satisfaction (mock for now) #TODO: Replace with actual calculation
    # This should be replaced with actual logic to calculate customer satisfaction based on ratings or feedback
    customer_satisfaction = {
        'average_rating': 4.2,
        'total_ratings': 156,
        'distribution': {
            '5': 78,
            '4': 45,
            '3': 20,
            '2': 8,
            '1': 5
        }
    }
    
    return {
        'summary': summary,
        'trends': trends,
        'channel_distribution': channel_distribution,
        'agent_performance': agent_performance,
        'peak_hours': peak_hours,
        'response_times': response_times,
        'customer_satisfaction': customer_satisfaction,
    }

def get_conversation_trends(queryset, granularity='day'):
    """Get conversation trends over time"""
    
    # Choose truncation based on granularity
    trunc_funcs = {
        'hour': TruncHour,
        'day': TruncDate,
        'week': TruncWeek,
        'month': TruncMonth,
    }
    
    trunc_func = trunc_funcs.get(granularity, TruncDate)
    
    trends = queryset.annotate(
        period=trunc_func('started_at')
    ).values('period').annotate(
        conversations=Count('id'),
        messages=Sum('message_count'),
        unique_customers=Count('customer_phone', distinct=True),
        handoffs=Count('handed_off_at')
    ).order_by('period')
    
    return list(trends)

def get_agent_performance(organization, date_from, date_to):
    """Get performance metrics for each agent"""
    
    agents = Agent.objects.filter(
        organization=organization,
        is_active=True
    )
    
    performance = []
    for agent in agents:
        conversations = Conversation.objects.filter(
            agent=agent,
            started_at__gte=date_from,
            started_at__lte=date_to
        )
        
        # Calculate average response time
        avg_response_time = conversations.filter(
            first_response_time_seconds__isnull=False
        ).aggregate(
            avg=Avg('first_response_time_seconds')
        )['avg'] or 0
        
        performance.append({
            'agent_id': str(agent.id),
            'agent_name': agent.name,
            'total_conversations': conversations.count(),
            'total_messages': conversations.aggregate(
                total=Sum('message_count')
            )['total'] or 0,
            'avg_messages_per_conversation': conversations.aggregate(
                avg=Avg('message_count')
            )['avg'] or 0,
            'handoff_rate': (conversations.filter(handed_off_at__isnull=False).count() / 
                           max(conversations.count(), 1)) * 100,
            'avg_response_time_seconds': avg_response_time,
            'channels': list(conversations.values('channel').annotate(
                count=Count('id')
            )),
        })
    
    return performance

def get_peak_hours(queryset):
    """Analyze peak conversation hours"""
    
    peak_hours = queryset.annotate(
        hour=ExtractHour('started_at')
    ).values('hour').annotate(
        count=Count('id'),
        avg_messages=Avg('message_count')
    ).order_by('hour')
    
    return list(peak_hours)

def get_response_times(queryset):
    """Analyze response time metrics"""
    
    response_times = queryset.filter(
        first_response_time_seconds__isnull=False
    ).aggregate(
        avg_first_response=Avg('first_response_time_seconds'),
        min_first_response=Min('first_response_time_seconds'),
        max_first_response=Max('first_response_time_seconds'),
    )
    
    # Calculate response time buckets
    buckets = {
        'under_1_min': queryset.filter(
            first_response_time_seconds__lt=60
        ).count(),
        '1_to_5_min': queryset.filter(
            first_response_time_seconds__gte=60,
            first_response_time_seconds__lt=300
        ).count(),
        '5_to_15_min': queryset.filter(
            first_response_time_seconds__gte=300,
            first_response_time_seconds__lt=900
        ).count(),
        'over_15_min': queryset.filter(
            first_response_time_seconds__gte=900
        ).count(),
    }
    
    response_times['distribution'] = buckets
    return response_times


@router.get("/conversation-flow", auth=auth)
def get_conversation_flow(request, date_from: datetime = None, date_to: datetime = None):
    """Analyze conversation flow and status transitions"""
    
    user = request.auth
    
    if not date_to:
        date_to = timezone.now()
    if not date_from:
        date_from = date_to - timedelta(days=7)
    
    queryset = Conversation.objects.filter(
        agent__organization=user.organization,
        started_at__gte=date_from,
        started_at__lte=date_to
    )
    
    # Status distribution
    status_distribution = queryset.values('status').annotate(
        count=Count('id'),
        avg_duration=Avg(
            ExpressionWrapper(
                F('ended_at') - F('started_at'),
                output_field=DurationField()
            )
        )
    )
    
    # Handoff analysis
    handoff_queryset = queryset.filter(handed_off_at__isnull=False)
    handoff_analysis = {
        'total_handoffs': handoff_queryset.count(),
        
        # --- FIX APPLIED HERE ---
        # Evaluate the queryset into a list of dictionaries
        'handoff_reasons': list(
            handoff_queryset.values('metadata__handoff_reason').annotate(
                count=Count('id')
            )
        ),
        
        'avg_time_to_handoff': handoff_queryset.aggregate(
            avg=Avg(
                ExpressionWrapper(
                    F('handed_off_at') - F('started_at'),
                    output_field=DurationField()
                )
            )
        )['avg'],
    }
    
    return {
        'status_distribution': list(status_distribution),
        'handoff_analysis': handoff_analysis,
    }



@router.get("/customer-insights", auth=auth)
def get_customer_insights(request, date_from: datetime = None, date_to: datetime = None):
    """Get insights about customer behavior"""
    
    user = request.auth
    
    if not date_to:
        date_to = timezone.now()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    
    queryset = Conversation.objects.filter(
        agent__organization=user.organization,
        started_at__gte=date_from,
        started_at__lte=date_to
    )
    
    # Top customers by conversation count
    top_customers = queryset.values('customer_phone', 'customer_name').annotate(
        conversation_count=Count('id'),
        total_messages=Sum('message_count'),
        channels_used=Count('channel', distinct=True)
    ).order_by('-conversation_count')[:10]
    
    # Returning customers
    customer_conversations = queryset.values('customer_phone').annotate(
        count=Count('id')
    )
    
    returning_customers = customer_conversations.filter(count__gt=1).count()
    new_customers = customer_conversations.filter(count=1).count()
    
    # Average conversation length by customer type
    avg_conversation_length = {
        'new_customers': queryset.filter(
            customer_phone__in=customer_conversations.filter(count=1).values('customer_phone')
        ).aggregate(avg=Avg('message_count'))['avg'] or 0,
        'returning_customers': queryset.filter(
            customer_phone__in=customer_conversations.filter(count__gt=1).values('customer_phone')
        ).aggregate(avg=Avg('message_count'))['avg'] or 0,
    }
    
    return {
        'top_customers': list(top_customers),
        'customer_distribution': {
            'new': new_customers,
            'returning': returning_customers,
            'return_rate': (returning_customers / max(new_customers + returning_customers, 1)) * 100,
        },
        'avg_conversation_length': avg_conversation_length,
    }

####################################################
###########! Time-Series Export API ###########
####################################################

from apps.analytics.models import HourlyMetrics, DailyMetrics

class ExportParams(Schema):
    start_date: datetime
    end_date: datetime
    format: str = 'json'  # json, csv
    metrics: Optional[list[str]] = None  # specific metrics to export
    granularity: str = 'hourly'  # hourly, daily

@router.post("/export/time-series", auth=auth)
def export_time_series(request, params: ExportParams):
    """Export time-series metrics data"""
    
    user = request.auth
    
    # Choose the right model based on granularity
    if params.granularity == 'daily':
        model = DailyMetrics
        queryset = model.objects.filter(
            organization=user.organization,
            date__gte=params.start_date.date(),
            date__lte=params.end_date.date()
        )
    else:
        model = HourlyMetrics
        queryset = model.objects.filter(
            organization=user.organization,
            timestamp__gte=params.start_date,
            timestamp__lte=params.end_date
        )
    
    # Order by time
    queryset = queryset.order_by('timestamp' if params.granularity == 'hourly' else 'date')
    
    if params.format == 'csv':
        return export_as_csv(queryset, params.metrics)
    else:
        return export_as_json(request, queryset, params.metrics)

def export_as_csv(queryset, metrics=None):
    """Export queryset as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="metrics_{datetime.now():%Y%m%d}.csv"'
    
    if not queryset.exists():
        return response
    
    # Get fields to export
    fields = metrics or [
        'timestamp', 'total_conversations', 'total_messages',
        'active_conversations', 'avg_response_time_seconds'
    ]
    
    writer = csv.DictWriter(response, fieldnames=fields)
    writer.writeheader()
    
    for obj in queryset:
        row = {}
        for field in fields:
            value = getattr(obj, field, '')
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            row[field] = value
        writer.writerow(row)
    
    return response

def export_as_json(request, queryset, metrics=None):
    """Export queryset as JSON"""
    data = []
    
    for obj in queryset:
        row = {}
        if metrics:
            for field in metrics:
                value = getattr(obj, field, None)
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                row[field] = value
        else:
            # Export all fields
            for field in obj._meta.get_fields():
                if field.concrete and not field.many_to_many:
                    value = getattr(obj, field.name, None)
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif hasattr(value, 'id'):
                        value = str(value.id)
                    row[field.name] = value
        data.append(row)
    
    return {
        'export_date': datetime.now().isoformat(),
        'organization': str(request.auth.organization.id),
        'granularity': 'hourly' if 'HourlyMetrics' in str(queryset.model) else 'daily',
        'total_records': len(data),
        'data': data
    }

@router.get("/time-series/{metric_name}", auth=auth)
def get_time_series(
    request, 
    metric_name: str,
    start_date: datetime = None,
    end_date: datetime = None,
    granularity: str = 'hourly'
):
    """Get time-series data for a specific metric"""
    
    user = request.auth
    
    # Default to last 7 days
    if not end_date:
        end_date = timezone.now()
    if not start_date:
        start_date = end_date - timedelta(days=7)
    
    if granularity == 'daily':
        queryset = DailyMetrics.objects.filter(
            organization=user.organization,
            date__gte=start_date.date(),
            date__lte=end_date.date()
        ).order_by('date')
        
        data = [
            {
                'date': obj.date.isoformat(),
                'value': getattr(obj, metric_name, 0)
            }
            for obj in queryset
        ]
    else:
        queryset = HourlyMetrics.objects.filter(
            organization=user.organization,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        data = [
            {
                'timestamp': obj.timestamp.isoformat(),
                'value': getattr(obj, metric_name, 0)
            }
            for obj in queryset
        ]
    
    return {
        'metric': metric_name,
        'granularity': granularity,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'data': data
    }