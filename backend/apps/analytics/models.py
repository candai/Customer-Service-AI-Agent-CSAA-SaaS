# backend/apps/analytics/models.py
from django.db import models
from apps.accounts.models import Organization
from apps.agents.models import Agent

class HourlyMetrics(models.Model):
    """Store aggregated metrics per hour for trend analysis"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # Conversation metrics
    total_conversations = models.IntegerField(default=0)
    active_conversations = models.IntegerField(default=0)
    ended_conversations = models.IntegerField(default=0)
    handed_off_conversations = models.IntegerField(default=0)
    
    # Message metrics
    total_messages = models.IntegerField(default=0)
    ai_messages = models.IntegerField(default=0)
    human_messages = models.IntegerField(default=0)
    customer_messages = models.IntegerField(default=0)
    
    # Performance metrics
    avg_response_time_seconds = models.FloatField(default=0)
    avg_conversation_duration_minutes = models.FloatField(default=0)
    avg_messages_per_conversation = models.FloatField(default=0)
    
    # Channel breakdown
    whatsapp_conversations = models.IntegerField(default=0)
    sms_conversations = models.IntegerField(default=0)
    voice_conversations = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['organization', 'agent', 'timestamp']
        indexes = [
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['agent', 'timestamp']),
        ]

class DailyMetrics(models.Model):
    """Daily rollup of metrics for longer-term storage"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    
    # Same metrics as hourly but aggregated for the day
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    unique_customers = models.IntegerField(default=0)
    
    # Cost tracking
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    whatsapp_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sms_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    voice_minutes = models.IntegerField(default=0)
    voice_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['organization', 'date']