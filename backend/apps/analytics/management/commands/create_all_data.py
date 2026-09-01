# backend/apps/analytics/management/commands/create_fake_data.py
from time import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, timedelta
import random
from apps.conversations.models import Conversation, Message
from apps.agents.models import Agent
from apps.accounts.models import Organization
from apps.analytics.models import HourlyMetrics, DailyMetrics

class Command(BaseCommand):
    help = 'Generate fake analytics data for testing'
    
    def handle(self, *args, **options):
        
        # Get first organization and agents
        org = Organization.objects.first()
        if not org:
            self.stdout.write(self.style.ERROR('No organization found. Create one first.'))
            return
            
        agents = Agent.objects.filter(organization=org)
        if not agents.exists():
            self.stdout.write(self.style.ERROR('No agents found. Create some agents first.'))
            return
        
        # Clear all existing data
        self.stdout.write('Clearing all existing data...')
        Conversation.objects.filter(agent__organization=org).delete()
        HourlyMetrics.objects.filter(organization=org).delete()
        DailyMetrics.objects.filter(organization=org).delete()
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))