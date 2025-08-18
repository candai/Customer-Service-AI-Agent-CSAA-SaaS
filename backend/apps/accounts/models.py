# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active=models.BooleanField(default=True)
    website = models.URLField(blank=True)
    
    # Billing/Limits
    subscription_tier = models.CharField(
        max_length=50, 
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    monthly_message_limit = models.IntegerField(default=1000)
    monthly_voice_minutes_limit = models.IntegerField(default=100)
    messages_used_this_month = models.IntegerField(default=0)
    voice_minutes_used_this_month = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        
    def __str__(self):
        return self.name



class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)  # Optional
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='users'
    )
    role = models.CharField(
        max_length=50, 
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('member', 'Member'),
        ], 
        default='member'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Profile
    avatar_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Timestamps
    last_login_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'  # Use email to login
    REQUIRED_FIELDS = []  # Remove email from required fields since it's the USERNAME_FIELD
    
    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return self.email or self.username