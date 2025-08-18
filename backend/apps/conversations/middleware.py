# apps/conversations/middleware.py
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from apps.accounts.models import User
import logging
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    """JWT auth middleware for WebSocket"""
    
    async def __call__(self, scope, receive, send):
        logger.info(f"JWTAuthMiddleware called for path: {scope.get('path')}")
        
        # Parse query string
        query_string = scope.get('query_string', b'').decode('utf-8')
        logger.info(f"Query string: {query_string}")
        
        # Extract token
        token = None
        if query_string:
            params = parse_qs(query_string)
            token_list = params.get('token', [])
            if token_list:
                token = token_list[0]
                logger.info(f"Token found: {token[:20]}...")
        
        # Authenticate and set user in scope
        if token:
            user = await self.get_user_from_token(token)
            scope['user'] = user
            logger.info(f"User set in scope: {user} (type: {type(user)})")
            if not isinstance(user, AnonymousUser):
                logger.info(f"User email: {user.email}, Has org: {hasattr(user, 'organization')}")
        else:
            logger.info("No token, setting AnonymousUser")
            scope['user'] = AnonymousUser()
        
        # IMPORTANT: Call the inner application with the modified scope
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token_str):
        """Validate token and get user"""
        try:
            # Remove any whitespace
            token_str = token_str.strip()
            
            # Validate token
            access_token = AccessToken(token_str)
            
            # Get user with organization
            user_id = access_token.get('user_id')
            user = User.objects.select_related('organization').get(id=user_id)
            
            logger.info(f"✅ Authenticated WebSocket user: {user.email}")
            return user
            
        except TokenError as e:
            logger.error(f"Token validation error: {e}")
            return AnonymousUser()
        except User.DoesNotExist:
            logger.error(f"User not found for token")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return AnonymousUser()