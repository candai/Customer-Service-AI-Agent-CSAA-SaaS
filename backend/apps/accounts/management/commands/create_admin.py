# apps/accounts/management/commands/create_admin.py
from django.core.management.base import BaseCommand
from apps.accounts.models import User, Organization

class Command(BaseCommand):
    help = 'Create a superuser with an organization'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--org', type=str, default='Admin Organization')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        org_name = options['org']
        
        # Create organization
        org, _ = Organization.objects.get_or_create(
            name=org_name,
            defaults={'subscription_tier': 'enterprise'}
        )
        
        # Create superuser
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User {email} already exists'))
            return
            
        user = User.objects.create_superuser(
            email=email,
            username=email,
            password=password,
            organization=org,
            role='owner'
        )
        
        self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully'))