# test_token_validation.py
import django
import os
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from apps.accounts.models import User
from django.conf import settings

def test_token_flow():
    print("Testing JWT token creation and validation...")
    print(f"ACCESS_TOKEN_LIFETIME: {settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']}")
    print(f"SECRET_KEY exists: {bool(settings.SECRET_KEY)}")
    print(f"SECRET_KEY first 10 chars: {settings.SECRET_KEY[:10]}...")
    
    # Get a test user
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users in database")
            return
        
        print(f"✅ Using user: {user.email}")
        
        # Create tokens
        refresh = RefreshToken.for_user(user)
        access_token_str = str(refresh.access_token)
        
        print(f"✅ Token created: {access_token_str[:50]}...")
        
        # Now try to validate it immediately
        try:
            validated_token = AccessToken(access_token_str)
            print(f"✅ Token validated successfully!")
            print(f"   User ID in token: {validated_token['user_id']}")
            print(f"   Token type: {validated_token['token_type']}")
            print(f"   Expiration: {datetime.fromtimestamp(validated_token['exp'])}")
            
            # Try to get the user
            user_id = validated_token['user_id']
            found_user = User.objects.get(id=user_id)
            print(f"✅ User found from token: {found_user.email}")
            
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_token_flow()