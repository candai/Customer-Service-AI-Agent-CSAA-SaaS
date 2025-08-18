# apps/conversations/admin.py
from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['customer_phone', 'agent', 'channel', 'status', 'started_at']
    list_filter = ['status', 'channel', 'started_at']
    search_fields = ['customer_phone', 'customer_name']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender_type', 'message_type', 'created_at']
    list_filter = ['sender_type', 'message_type', 'created_at']
    search_fields = ['content']