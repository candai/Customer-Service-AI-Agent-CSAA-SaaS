# apps/agents/models.py
from django.db import models
import uuid

class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'accounts.Organization', 
        on_delete=models.CASCADE, 
        related_name='agents'
    )
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField()
    avatar_url = models.URLField(blank=True, null=True)
    
    # AI Configuration
    system_prompt = models.TextField(
        help_text="Base instructions for the AI agent"
    )
    personality_traits = models.TextField(
        help_text="How should the agent behave?"
    )
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=500)
    model = models.CharField(
        max_length=50,
        choices=[
            ('gpt-4', 'GPT-4'),
            ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ],
        default='gpt-4'
    )
    
    # Voice Configuration (for phone calls)
    voice_id = models.CharField(
        max_length=100, 
        default='21m00Tcm4TlvDq8ikWAM', # Rachel
        help_text="ElevenLabs voice ID"
    )
    voice_settings = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Voice configuration settings"
    )
    
    # Channel Configuration
    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_number = models.CharField(
        max_length=20, 
        blank=True, 
        unique=True, 
        null=True,
        db_index=True
    )
    
    sms_enabled = models.BooleanField(default=False)
    sms_number = models.CharField(
        max_length=20, 
        blank=True, 
        unique=True, 
        null=True,
        db_index=True
    )
    
    voice_enabled = models.BooleanField(default=False)
    voice_number = models.CharField(
        max_length=20, 
        blank=True, 
        unique=True, 
        null=True,
        db_index=True
    )
    
    # Response Configuration
    response_delay_seconds = models.IntegerField(
        default=2, 
        help_text="Simulate typing delay"
    )
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='ET')
    
    # Business Hours (JSON structure)
    business_hours = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text='{"monday": {"start": "09:00", "end": "17:00"}, ...}'
    )
    out_of_hours_message = models.TextField(blank=True, null=True, help_text="Message when outside business hours")
    
    # Welcome Messages
    welcome_message = models.TextField(
        default="Hello! How can I help you today?",
        help_text="Initial greeting message"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=False)
    
    # Metrics
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    average_conversation_duration = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'agents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    

# AgentTemplate Model (Optional - for quick agent creation)
class AgentTemplate(models.Model):
    """Pre-configured templates for quick agent creation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('customer_service', 'Customer Service'),
            ('sales', 'Sales'),
            ('support', 'Technical Support'),
            ('booking', 'Appointment Booking'),
            ('faq', 'FAQ Bot'),
        ]
    )
    
    # Template Configuration
    system_prompt = models.TextField()
    personality_traits = models.TextField()
    suggested_knowledge = models.JSONField(default=list)
    
    # Public/Private
    is_public = models.BooleanField(default=True)
    organization = models.ForeignKey(
        'accounts.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If private template"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'agent_templates'



class KnowledgeDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent, 
        on_delete=models.CASCADE, 
        related_name='knowledge_documents'
    )
    
    # Document Information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    document_type = models.CharField(
        max_length=50, 
        choices=[
            ('text', 'Plain Text'),
            ('pdf', 'PDF'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('url', 'Website URL'),
        ]
    )
    
    # Storage
    file = models.FileField(
        upload_to='knowledge_documents/%Y/%m/%d/', 
        null=True, 
        blank=True
    )
    source_url = models.URLField(blank=True, null=True, help_text="If document is from a URL")
    
    # Processed content for AI
    content = models.TextField(help_text="Extracted text content")
    content_hash = models.CharField(
        max_length=64, 
        blank=True,
        null=True,
        help_text="SHA256 hash to detect duplicates"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Additional metadata about the document"
    )
    
    # Processing Status
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    # Vector embeddings for semantic search (optional for now)
    embeddings = models.JSONField(null=True, blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'knowledge_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['agent', 'is_processed']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.agent.name}"