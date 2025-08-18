# apps/accounts/permissions.py
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja"""
    
    def authenticate(self, request, token):
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            if not user.is_active:
                return None
            
            return user
        except InvalidToken:
            return None
        except Exception:
            return None

class OrganizationOwnerAuth(JWTAuth):
    """Authentication that requires organization owner role"""
    
    def authenticate(self, request, token):
        user = super().authenticate(request, token)
        
        if user and user.role == 'owner':
            return user
        
        return None

class OrganizationMemberAuth(JWTAuth):
    """Authentication that requires organization membership"""
    
    def authenticate(self, request, token):
        user = super().authenticate(request, token)
        
        if user and user.organization:
            return user
        
        return None