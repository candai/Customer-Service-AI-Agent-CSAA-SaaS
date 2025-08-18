# apps/agents/admin.py
from django.contrib import admin
from .models import Agent, KnowledgeDocument

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'is_active', 'total_conversations', 'created_at']
    list_filter = ['is_active', 'whatsapp_enabled', 'sms_enabled', 'voice_enabled']
    search_fields = ['name', 'description']

@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'agent', 'document_type', 'is_processed', 'uploaded_at']
    list_filter = ['document_type', 'is_processed']
    search_fields = ['title', 'content']