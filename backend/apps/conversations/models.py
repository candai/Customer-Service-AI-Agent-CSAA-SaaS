# apps/conversations/models.py
from django.db import models
import uuid
from django.utils import timezone
# auto_add_now -> timezone.now
# django warning: conversations.Message.created_at: (fields.W161) Fixed default value provided.
# 	HINT: It seems you set a fixed date / time / datetime value as default for this field. This may not be what you want. If you want to have the current date as default, use `django.utils.timezone.now`
########! CONVERSATION MODEL !#########
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        'agents.Agent', 
        on_delete=models.CASCADE, 
        related_name='conversations'
    )
    
    # Channel Information
    channel = models.CharField(
        max_length=20, 
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('sms', 'SMS'),
            ('voice', 'Voice Call'),
        ],
        db_index=True
    )
    
    # Customer Information
    customer_phone = models.CharField(max_length=20, db_index=True)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional customer information"
    )
    
    # Conversation State
    status = models.CharField(
        max_length=20, 
        choices=[
            ('active', 'Active'),
            ('waiting', 'Waiting for Customer'),
            ('ended', 'Ended'),
            ('handed_off', 'Handed Off to Human'),
            ('abandoned', 'Abandoned'),
        ], 
        default='active',
        db_index=True
    )
    
    # Assignment (for handoff)
    assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations'
    )
    
    # Timestamps
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    handed_off_at = models.DateTimeField(null=True, blank=True)
    
    # Metrics
    message_count = models.IntegerField(default=0)
    customer_message_count = models.IntegerField(default=0)
    agent_message_count = models.IntegerField(default=0)
    
    # Analysis
    sentiment_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Overall sentiment (-1 to 1)"
    )
    satisfaction_rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        help_text="Customer satisfaction rating (1-5)"
    )
    
    # Performance Metrics
    first_response_time_seconds = models.IntegerField(null=True, blank=True)
    resolution_time_seconds = models.IntegerField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conversation context and state"
    )
    
    # Tags and Categories
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags for categorization"
    )


    
    # External References
    external_id = models.CharField(
        max_length=255, 
        blank=True,
        help_text="External system reference (e.g., Twilio Call SID)"
    )
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['agent', 'status', 'started_at']),
            models.Index(fields=['customer_phone', 'started_at']),
            models.Index(fields=['channel', 'started_at']),
        ]
        
    def __str__(self):
        return f"{self.channel} - {self.customer_phone} - {self.status}"


#############! MESSAGE MODEL !#############
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    
    # Sender Information
    sender_type = models.CharField(
        max_length=20, 
        choices=[
            ('customer', 'Customer'),
            ('agent', 'AI Agent'),
            ('human', 'Human Agent'),
            ('system', 'System'),
        ],
        db_index=True
    )
    
    # Message Content
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, 
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('audio', 'Audio'),
            ('video', 'Video'),
            ('document', 'Document'),
            ('location', 'Location'),
            ('template', 'Template Message'),
        ], 
        default='text'
    )
    media_url = models.URLField(blank=True)
    media_mime_type = models.CharField(max_length=100, blank=True)
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional conversation metadata"
    )
    
    # External IDs (from Twilio, etc.)
    external_id = models.CharField(
        max_length=255, 
        blank=True,
        db_index=True,
        help_text="Message ID from external platform"
    )
    
    # Intent and Entities (from NLP processing)
    detected_intent = models.CharField(max_length=100, blank=True)
    detected_entities = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now(), db_index=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    # AI Processing
    ai_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="AI confidence score for generated responses"
    )
    tokens_used = models.IntegerField(
        default=0,
        help_text="Number of tokens used for AI processing"
    )
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['external_id']),
        ]
        
    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}..."