# apps/billing/api.py
from ninja import Router, Schema
from typing import List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from apps.accounts.api import auth
from apps.analytics.models import DailyMetrics, HourlyMetrics
from apps.accounts.models import Organization


router = Router(tags=["Billing"])

# Schemas
class UsageResponse(Schema):
    organization_name: str
    subscription_tier: str
    current_month_messages: int
    message_limit: int
    current_month_voice_minutes: int
    voice_limit: int
    total_cost_this_month: float

class UsageDetailResponse(Schema):
    date: datetime
    usage_type: str
    quantity: float
    cost: float
    agent_name: str

# Endpoints
@router.get("/usage", auth=auth)
def get_usage_summary(request):
    """Get usage summary for the current month"""
    
    user = request.auth
    org = user.organization
    
    # Get current month's start date
    now = timezone.now()
    month_start = datetime(now.year, now.month, 1)
    
    # Get usage from DailyMetrics instead of UsageLog
    metrics = DailyMetrics.objects.filter(
        organization=org,
        date__gte=month_start.date()
    ).aggregate(
        total_conversations=Sum('total_conversations'),
        total_messages=Sum('total_messages'),
        voice_minutes=Sum('voice_minutes'),
        total_cost=Sum('total_cost')
    )
    
    return {
        "organization_name": org.name,
        "subscription_tier": org.subscription_tier or 'free',
        "current_month_messages": metrics['total_messages'] or 0,
        "message_limit": org.monthly_message_limit or 1000,
        "current_month_voice_minutes": metrics['voice_minutes'] or 0,
        "voice_limit": org.monthly_voice_minutes_limit or 100,
        "total_cost_this_month": float(metrics['total_cost'] or 0)
    }

@router.get("/usage/details", auth=auth)
def get_usage_details(request, days: int = 30):
    """Get detailed usage breakdown by day"""
    
    user = request.auth
    org = user.organization
    since = timezone.now().date() - timedelta(days=days)
    
    daily_metrics = DailyMetrics.objects.filter(
        organization=org,
        date__gte=since
    ).order_by('-date')
    
    return [
        {
            "date": metric.date.isoformat(),
            "conversations": metric.total_conversations,
            "messages": metric.total_messages,
            "voice_minutes": metric.voice_minutes,
            "whatsapp_cost": float(metric.whatsapp_cost),
            "sms_cost": float(metric.sms_cost),
            "voice_cost": float(metric.voice_cost),
            "total_cost": float(metric.total_cost)
        }
        for metric in daily_metrics
    ]

@router.get("/usage/current", auth=auth)
def get_current_usage(request):
    """Get real-time usage for today"""
    
    user = request.auth
    org = user.organization
    today = timezone.now().date()
    
    # Get today's metrics from HourlyMetrics (more real-time)
    today_metrics = HourlyMetrics.objects.filter(
        organization=org,
        agent=None,  # Organization-wide
        timestamp__date=today
    ).aggregate(
        conversations=Sum('total_conversations'),
        messages=Sum('total_messages')
    )
    
    # Get month totals
    month_start = today.replace(day=1)
    month_metrics = DailyMetrics.objects.filter(
        organization=org,
        date__gte=month_start,
        date__lt=today  # Exclude today since we're getting it from hourly
    ).aggregate(
        conversations=Sum('total_conversations'),
        messages=Sum('total_messages'),
        voice_minutes=Sum('voice_minutes')
    )
    
    return {
        "today": {
            "conversations": today_metrics['conversations'] or 0,
            "messages": today_metrics['messages'] or 0,
        },
        "month_to_date": {
            "conversations": (month_metrics['conversations'] or 0) + (today_metrics['conversations'] or 0),
            "messages": (month_metrics['messages'] or 0) + (today_metrics['messages'] or 0),
            "voice_minutes": month_metrics['voice_minutes'] or 0,
        },
        "limits": {
            "messages": org.monthly_message_limit,
            "voice_minutes": org.monthly_voice_minutes_limit,
        },
        "percentage_used": {
            "messages": ((month_metrics['messages'] or 0) + (today_metrics['messages'] or 0)) / org.monthly_message_limit * 100 if org.monthly_message_limit else 0,
        }
    }

@router.get("/subscription", auth=auth)
def get_subscription_info(request):
   """Get subscription information"""
   
   user = request.auth
   org = user.organization
   
   # Define subscription tiers
   tiers = {
       'free': {
           'name': 'Free',
           'monthly_messages': 1000,
           'monthly_voice_minutes': 100,
           'agents': 1,
           'price': 0
       },
       'starter': {
           'name': 'Starter',
           'monthly_messages': 10000,
           'monthly_voice_minutes': 1000,
           'agents': 5,
           'price': 99
       },
       'professional': {
           'name': 'Professional',
           'monthly_messages': 50000,
           'monthly_voice_minutes': 5000,
           'agents': 20,
           'price': 299
       },
       'enterprise': {
           'name': 'Enterprise',
           'monthly_messages': -1,  # Unlimited
           'monthly_voice_minutes': -1,  # Unlimited
           'agents': -1,  # Unlimited
           'price': 999
       }
   }
   
   current_tier = tiers.get(org.subscription_tier, tiers['free'])
   
   return {
       "current_tier": current_tier,
       "all_tiers": tiers,
       "organization": {
           "name": org.name,
           "created_at": org.created_at
       }
   }

@router.post("/subscription/upgrade", auth=auth)
def upgrade_subscription(request, tier: str):
   """Upgrade subscription tier"""
   
   user = request.auth
   
   if user.role != 'owner':
       return 403, {"error": "Only organization owners can change subscription"}
   
   valid_tiers = ['free', 'starter', 'professional', 'enterprise']
   if tier not in valid_tiers:
       return 400, {"error": "Invalid subscription tier"}
   
   org = user.organization
   org.subscription_tier = tier
   
   # Update limits based on tier
   if tier == 'free':
       org.monthly_message_limit = 1000
       org.monthly_voice_minutes_limit = 100
   elif tier == 'starter':
       org.monthly_message_limit = 10000
       org.monthly_voice_minutes_limit = 1000
   elif tier == 'professional':
       org.monthly_message_limit = 50000
       org.monthly_voice_minutes_limit = 5000
   else:  # enterprise
       org.monthly_message_limit = 999999
       org.monthly_voice_minutes_limit = 999999
   
   org.save()
   
   return {"message": f"Successfully upgraded to {tier} tier"}