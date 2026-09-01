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
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Number of days of data to generate'
        )
    
    def handle(self, *args, **options):
        days_back = options['days']
        
        # Get first organization and agents
        org = Organization.objects.first()
        if not org:
            self.stdout.write(self.style.ERROR('No organization found. Create one first.'))
            return
            
        agents = Agent.objects.filter(organization=org)
        if not agents.exists():
            self.stdout.write(self.style.ERROR('No agents found. Create some agents first.'))
            return
        
        # Clear existing data
        self.stdout.write('Clearing existing fake data...')
        Conversation.objects.filter(agent__organization=org).delete()
        HourlyMetrics.objects.filter(organization=org).delete()
        DailyMetrics.objects.filter(organization=org).delete()
        
        # Generate data for each day
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        current_date = start_date
        while current_date <= end_date:
            print(f"Generating data for {current_date}")
            self.generate_day_data(org, agents, current_date)
            current_date += timedelta(days=1)

        
        # Run aggregation
        self.stdout.write('Running metrics aggregation...')
        from apps.analytics.tasks import aggregate_metrics, aggregate_daily_metrics
        
        # Aggregate hourly metrics
        hours_to_process = days_back * 24
        aggregate_metrics(hours_back=hours_to_process)
        
        # Aggregate daily metrics  
        aggregate_daily_metrics()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {days_back} days of fake data'))
    
    def generate_day_data(self, org, agents, date):
        day_of_week = date.weekday()
        print(f"Generating data for {date} (Day {day_of_week})")
        if day_of_week in [5, 6]:
            num_conversations = random.randint(20, 40)
        else:
            num_conversations = random.randint(50, 100)
            
        conversations_to_create = []
        messages_to_create = []

        for _ in range(num_conversations):
            hour_weights = [1, 1, 1, 1, 1, 1, 2, 3, 5, 8, 8, 7, 6, 7, 8, 8, 7, 5, 3, 2, 1, 1, 1, 1]
            hour = random.choices(range(24), weights=hour_weights)[0]
            minute = random.randint(0, 59)
            
            start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if start_time > timezone.now():
                continue
            
            duration_minutes = random.randint(5, 30)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            message_count = random.randint(5, 25)
            
            is_handed_off = random.choices([True, False], weights=[10, 90])[0]
            handed_off_at_time = start_time + timedelta(minutes=random.randint(2, 10)) if is_handed_off else None
            
            if end_time >= timezone.now():
                final_status = 'active'
                ended_at_time = None
            elif is_handed_off:
                final_status = 'handed_off'
                ended_at_time = end_time
            else:
                final_status = 'ended'
                ended_at_time = end_time

            conversation = Conversation(
                agent=random.choice(agents),
                customer_phone=f"+1555{random.randint(1000000, 9999999)}",
                customer_name=f"Customer {random.randint(1000, 9999)}",
                channel=random.choice(['whatsapp', 'whatsapp', 'sms', 'voice']),
                status=final_status,
                started_at=start_time,
                ended_at=ended_at_time,
                first_response_time_seconds=random.randint(1, 30),
                message_count=message_count,
                handed_off_at=handed_off_at_time
            )
            conversations_to_create.append(conversation)

        created_conversations = Conversation.objects.bulk_create(conversations_to_create, ignore_conflicts=True)
        
        for conv in created_conversations:
            duration_minutes = (conv.ended_at - conv.started_at).total_seconds() / 60 if conv.ended_at else 30
            for i in range(conv.message_count):
                msg_time = conv.started_at + timedelta(minutes=i * (duration_minutes / conv.message_count))
                sender_type = 'customer' if i % 2 == 0 else 'agent'
                
                message = Message(
                    conversation=conv,
                    sender_type=sender_type,
                    content=self.get_sample_message(sender_type),
                    created_at=msg_time
                )
                messages_to_create.append(message)

        if messages_to_create:
            Message.objects.bulk_create(messages_to_create, ignore_conflicts=True)

        self.stdout.write(f'Generated {len(created_conversations)} conversations for {date.today()}')

    def get_sample_message(self, sender_type):
        """Get sample message content"""
        customer_messages = [
            "Hi, I need help with my order",
            "Can you check my account?",
            "When will my package arrive?",
            "I have a problem with the product",
            "How do I return this item?",
            "Is this product available?",
            "What are your business hours?",
            "I need to speak to someone",
            "Can you help me with pricing?",
            "Thank you for your help!"
        ]
        
        agent_messages = [
            "Hello! I'd be happy to help you with that.",
            "Let me check that for you.",
            "I can see your order here.",
            "Your package is scheduled to arrive tomorrow.",
            "I understand your concern.",
            "Here's what I can do for you.",
            "Is there anything else I can help with?",
            "Thank you for contacting us!",
            "I've updated your account.",
            "The issue has been resolved."
        ]
        
        if sender_type == 'customer':
            return random.choice(customer_messages)
        else:
            return random.choice(agent_messages)