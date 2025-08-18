# apps/accounts/api.py
from ninja import Router, Schema
from ninja.security import HttpBearer
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from typing import Optional
from datetime import datetime
from .models import User, Organization
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken

router = Router(tags=["Authentication"])

# Schemas
class LoginRequest(Schema):
    email: str
    password: str

class LoginResponse(Schema):
    access: str
    refresh: str
    user_id: str
    organization_id: Optional[str]
    role: str
    email: str
    name: str

class RegisterRequest(Schema):
    email: str
    password: str
    organization_name: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None

class RefreshRequest(Schema):
    refresh: str

# JWT Bearer Authentication
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            # Validate the token
            validated_token = AccessToken(token)
            
            # Get the user
            user_id = validated_token['user_id']
            user = User.objects.select_related('organization').get(id=user_id)
            request.user = user
            
            if not user.is_active:
                return None
                
            return user
        except (TokenError, User.DoesNotExist):
            return None

auth = JWTAuth()

# Endpoints
@router.post("/login", response={200: LoginResponse, 400: dict})
def login(request, data: LoginRequest):
    """Authenticate user and return JWT tokens"""
    
    # Authenticate using email
    user = authenticate(request, username=data.email, password=data.password)
    
    if not user:
        return 400, {"error": "Invalid email or password"}
    
    if not user.is_active:
        return 400, {"error": "Account is disabled"}
    
    # Update last login
    user.last_login_at = timezone.now()
    user.save(update_fields=['last_login_at'])
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims to token
    refresh['email'] = user.email
    refresh['role'] = user.role
    refresh['organization_id'] = str(user.organization.id) if user.organization else None
    
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user_id": str(user.id),
        "organization_id": str(user.organization.id) if user.organization else None,
        "role": user.role,
        "email": user.email,
        "name": f"{user.first_name} {user.last_name}".strip() or user.email
    }

@router.post("/register", response={201: LoginResponse, 400: dict})
@transaction.atomic
def register(request, data: RegisterRequest):
    """Register a new user and organization"""
    
    # Validate email doesn't exist
    if User.objects.filter(email=data.email).exists():
        return 400, {"error": "Email already registered"}
    
    try:
        # Create organization first
        org = Organization.objects.create(
            name=data.organization_name
        )
        
        # Create user
        user = User.objects.create(
            email=data.email,
            username=data.email,  # Use email as username
            password=make_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number or "",
            organization=org,
            role='owner',
            is_active=True
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['organization_id'] = str(org.id)
        
        return 201, {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": str(user.id),
            "organization_id": str(org.id),
            "role": user.role,
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}".strip()
        }
        
    except Exception as e:
        # Rollback will happen automatically due to @transaction.atomic
        return 400, {"error": f"Registration failed: {str(e)}"}

@router.post("/refresh", response={200: dict, 400: dict})
def refresh_token(request, data: RefreshRequest):
    """Refresh JWT access token"""
    try:
        refresh = RefreshToken(data.refresh)
        
        # You can add token rotation here if wanted
        # refresh.blacklist()  # Blacklist old refresh token
        # new_refresh = RefreshToken.for_user(refresh.user)
        
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)  # Or new_refresh if rotating
        }
    except TokenError as e:
        return 400, {"error": "Invalid or expired refresh token"}
    
@router.post("/verify")
def verify_token(request, token: str):
    """Verify if token is still valid"""
    
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        
        # Check if token is close to expiry (within 5 minutes)
        exp = datetime.fromtimestamp(access_token['exp'])
        now = datetime.now()
        time_until_expiry = (exp - now).total_seconds()
        
        return {
            'valid': True,
            'user_id': user_id,
            'expires_in': time_until_expiry,
            'should_refresh': time_until_expiry < 300  # Less than 5 minutes
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}

@router.post("/logout", response={200: dict}, auth=auth)
def logout(request):
    """Logout user (optionally blacklist token)"""
    try:
        # If you want to blacklist tokens, you need to install:
        # pip install djangorestframework-simplejwt[blacklist]
        # And add 'rest_framework_simplejwt.token_blacklist' to INSTALLED_APPS
        
        # For now, just return success
        # The client should remove the token from storage
        return {"message": "Successfully logged out"}
    except Exception as e:
        return {"message": "Logout successful"}

@router.get("/me", response={200: dict}, auth=auth)
def get_current_user(request):
    """Get current authenticated user info"""
    user = request.auth
    
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "role": user.role,
        "organization": {
            "id": str(user.organization.id),
            "name": user.organization.name,
            "subscription_tier": user.organization.subscription_tier
        } if user.organization else None
    }

@router.post("/change-password", response={200: dict, 400: dict}, auth=auth)
def change_password(request, current_password: str, new_password: str):
    """Change user password"""
    user = request.auth
    
    # Verify current password
    if not user.check_password(current_password):
        return 400, {"error": "Current password is incorrect"}
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Generate new tokens (optional - forces re-login)
    refresh = RefreshToken.for_user(user)
    
    return {
        "message": "Password changed successfully",
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }

@router.post("/forgot-password", response={200: dict, 400: dict})
def forgot_password(request, email: str):
    """Request password reset"""
    try:
        user = User.objects.get(email=email)
        
        # TODO: Implement email sending with reset token
        # For now, just return success
        
        return {"message": "Password reset instructions sent to your email"}
    except User.DoesNotExist:
        # Don't reveal if email exists or not for security
        return {"message": "Password reset instructions sent to your email"}