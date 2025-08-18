import sys
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from rest_framework_simplejwt.tokens import AccessToken
import jwt


token = sys.argv[1] if len(sys.argv) > 1 else input("Enter token: ")

try:
    # Try to decode without validation first
    
    
    # Decode without verification to see contents
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"Token contents (unverified): {decoded}")
    
    # Now try with verification
    access_token = AccessToken(token)
    print(f"✅ Token is valid!")
    print(f"User ID: {access_token['user_id']}")
    
except Exception as e:
    print(f"❌ Error: {e}")