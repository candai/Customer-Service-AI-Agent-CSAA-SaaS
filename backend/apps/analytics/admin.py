from django.contrib import admin
from apps.analytics.models import *

@admin.register(HourlyMetrics)
class HourlyMetricsAdmin(admin.ModelAdmin):
    list_display = ['organization', 'agent', 'timestamp', 'total_conversations', 'total_messages', 'whatsapp_conversations', 'sms_conversations', 'voice_conversations', 'created_at']

@admin.register(DailyMetrics)
class DailyMetricsAdmin(admin.ModelAdmin):
    list_display = ['organization', 'date', 'total_conversations', 'total_messages', 'voice_minutes', 'total_cost']
    list_filter = ['organization', 'date']
    search_fields = ['organization__name']