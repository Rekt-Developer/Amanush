from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Optional
import logging
import re

from app.core.config import get_settings
from app.application.services.auth_service import AuthService
from app.application.services.jwt import get_jwt_manager
from app.infrastructure.repositories.user_repository import MongoUserRepository
from app.domain.models.user import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests"""
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.settings = get_settings()
        self.auth_service = AuthService(MongoUserRepository())
        
        # Default paths that don't require authentication
        self.excluded_paths = excluded_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/status",
            "/api/v1/auth/refresh",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication for each request"""
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check if this is a resource access request with token parameter
        if self._is_resource_access_with_token(request):
            return await call_next(request)
        
        # Skip authentication if auth_provider is 'none'
        if self.settings.auth_provider == "none":
            # Add anonymous user to request state
            request.state.user = User(
                id="anonymous",
                username="anonymous",
                is_active=True
            )
            return await call_next(request)
        
        # Extract authentication information
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response("Missing Authorization header")
        
        try:
            # For basic auth
            if auth_header.startswith("Basic "):
                user = await self._handle_basic_auth(auth_header)
            # For bearer token (if implemented)
            elif auth_header.startswith("Bearer "):
                user = await self._handle_bearer_auth(auth_header)
            else:
                return self._unauthorized_response("Invalid authentication scheme")
            
            if not user:
                return self._unauthorized_response("Authentication failed")
            
            if not user.is_active:
                return self._unauthorized_response("User account is inactive")
            
            # Add user to request state
            request.state.user = user
            
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return self._unauthorized_response("Authentication failed")
    
    async def _handle_basic_auth(self, auth_header: str) -> Optional[User]:
        """Handle HTTP Basic Authentication"""
        try:
            import base64
            
            # Extract credentials
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(":", 1)
            
            # Authenticate user
            user = await self.auth_service.authenticate_user(username, password)
            return user
            
        except Exception as e:
            logger.warning(f"Basic auth failed: {e}")
            return None
    
    async def _handle_bearer_auth(self, auth_header: str) -> Optional[User]:
        """Handle Bearer Token Authentication"""
        try:
            # Extract token
            token = auth_header.split(" ")[1]
            
            # Verify token and get user
            user = await self.auth_service.verify_token(token)
            return user
            
        except Exception as e:
            logger.warning(f"Bearer token auth failed: {e}")
            return None
    
    def _is_resource_access_with_token(self, request: Request) -> bool:
        """Check if request is resource access with valid token parameter"""
        try:
            # Check if token parameter exists
            token = request.query_params.get("token")
            if not token:
                return False
            
            # Determine resource type and ID based on URL pattern
            resource_type = None
            resource_id = None
            
            # File download: GET /api/v1/files/{file_id}
            file_download_pattern = r'^/api/v1/files/([^/]+)/?$'
            if request.method == "GET":
                file_match = re.match(file_download_pattern, request.url.path)
                if file_match:
                    resource_type = "file"
                    resource_id = file_match.group(1)
            
            # VNC WebSocket: WebSocket /api/v1/sessions/{session_id}/vnc
            vnc_pattern = r'^/api/v1/sessions/([^/]+)/vnc/?$'
            vnc_match = re.match(vnc_pattern, request.url.path)
            if vnc_match:
                resource_type = "vnc"
                resource_id = vnc_match.group(1)
            
            # If no matching pattern found
            if not resource_type or not resource_id:
                return False
            
            # Verify the resource access token
            jwt_manager = get_jwt_manager()
            token_payload = jwt_manager.verify_resource_access_token(token, resource_type, resource_id)
            
            if token_payload:
                logger.info(f"{resource_type.upper()} access authenticated via token for {resource_type}: {resource_id}")
                return True
            else:
                logger.warning(f"Invalid {resource_type} access token for {resource_type}: {resource_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking resource access token: {e}")
            return False

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return unauthorized response"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "code": 401,
                "msg": message,
                "data": None
            }
        )


def get_current_user(request: Request) -> User:
    """Get current authenticated user from request state"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.user 