# test_jwt_token.py
from rest_framework_simplejwt.tokens import AccessToken
from apps.accounts.models import User
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '.core.settings.base')
django.setup()

# Replace with your actual token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU0ODc1MTQ2LCJpYXQiOjE3NTQ4NzE1NDYsImp0aSI6ImViMjlmNjdmZDM1NTQ2OWU5MTYwMWUwOWY3MzhkNjI3IiwidXNlcl9pZCI6ImE3YmQyYzhhLTdiY2EtNGVlNy05OWUzLTVjOTZhZjI0ZTY0MCIsImVtYWlsIjoiY2FuZGFpMTk5NkBob3RtYWlsLmNvbSIsInJvbGUiOiJvd25lciIsIm9yZ2FuaXphdGlvbl9pZCI6ImM3ZDA0MDg0LTNiNTgtNDdiMC04N2Y1LTQyZDU0NWZhN2I4MCJ9.bJ0HEx33aSJaj7eVkHOc3GJqOddEaayGnY9e73ZovM4"

try:
    # Validate token
    access_token = AccessToken(token)
    user_id = access_token['user_id']
    
    # Get user
    user = User.objects.get(id=user_id)
    print(f"✅ Token is valid!")
    print(f"User: {user.email}")
    print(f"User ID: {user.id}")
    print(f"Organization: {user.organization.name if user.organization else 'None'}")
    
except Exception as e:
    print(f"❌ Token validation failed: {e}")