# UsageLog Model (For tracking and billing)
from django.db import models
import uuid

class UsageLog(models.Model):
    """Track usage for billing purposes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )
    
    # Usage Type
    usage_type = models.CharField(
        max_length=50,
        choices=[
            ('message', 'Message'),
            ('voice_minute', 'Voice Minute'),
            ('api_call', 'API Call'),
            ('storage', 'Storage'),
        ]
    )
    
    # Quantity
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Cost
    unit_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Reference
    conversation = models.ForeignKey(
        'conversations.Conversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usage_logs'
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]