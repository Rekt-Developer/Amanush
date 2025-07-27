import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from app.core.config import get_settings
from app.domain.models.user import User
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class JWTManager:
    """JWT token manager for authentication"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user"""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        
        payload = {
            "sub": user.id,  # Subject (user ID)
            "fullname": user.fullname,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "access"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created access token for user: {user.fullname}")
            return token
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user"""
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.settings.jwt_refresh_token_expire_days)
        
        payload = {
            "sub": user.id,  # Subject (user ID)
            "fullname": user.fullname,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "refresh"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created refresh token for user: {user.fullname}")
            return token
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check if token is not expired
            exp = payload.get("exp")
            if exp and exp < int(datetime.now(UTC).timestamp()):
                logger.warning("Token has expired")
                return None
            
            logger.debug(f"Token verified for user: {payload.get('fullname')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token"""
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        # Return user info from token payload
        return {
            "id": payload.get("sub"),
            "fullname": payload.get("fullname"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_active": payload.get("is_active", True),
            "token_type": payload.get("type", "access")
        }
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid"""
        return self.verify_token(token) is not None
    
    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """Get token expiration time"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, UTC)
        return None
    
    def create_resource_access_token(self, resource_type: str, resource_id: str, user_id: str, expire_minutes: int = 60) -> str:
        """Create JWT resource access token for URL-based access
        
        Args:
            resource_type: Type of resource (file, vnc, etc.)
            resource_id: ID of the resource (file_id, session_id, etc.)
            user_id: User ID who requested the token
            expire_minutes: Token expiration time in minutes
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=expire_minutes)
        
        payload = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "iat": int(now.timestamp()),  # Issued at (timestamp)
            "exp": int(expire.timestamp()),  # Expiration time (timestamp)
            "type": "resource_access"
        }
        
        try:
            token = jwt.encode(
                payload,
                self.settings.jwt_secret_key,
                algorithm=self.settings.jwt_algorithm
            )
            logger.debug(f"Created resource access token for {resource_type}: {resource_id}, user: {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create resource access token: {e}")
            raise
    
    def verify_resource_access_token(self, token: str, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """Verify resource access token for specific resource
        
        Args:
            token: JWT token to verify
            resource_type: Expected resource type (file, vnc, etc.)
            resource_id: Expected resource ID
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check if token is not expired
            exp = payload.get("exp")
            if exp and exp < int(datetime.now(UTC).timestamp()):
                logger.warning("Resource access token has expired")
                return None
            
            # Check if token type is resource_access
            if payload.get("type") != "resource_access":
                logger.warning("Invalid token type for resource access")
                return None
            
            # Check if token is for the requested resource type
            if payload.get("resource_type") != resource_type:
                logger.warning(f"Resource access token type mismatch: expected {resource_type}, got {payload.get('resource_type')}")
                return None
            
            # Check if token is for the requested resource ID
            if payload.get("resource_id") != resource_id:
                logger.warning(f"Resource access token ID mismatch for {resource_type}")
                return None
            
            logger.debug(f"Resource access token verified for {resource_type}: {resource_id}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Resource access token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid resource access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Resource access token verification failed: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        """Revoke token (placeholder for token blacklist implementation)"""
        # In a real implementation, you would add the token to a blacklist
        # stored in Redis or database with expiration time
        logger.info(f"Token revoked (placeholder implementation)")
        return True


@lru_cache()
def get_jwt_manager() -> JWTManager:
    """Get JWT manager instance"""
    return JWTManager()