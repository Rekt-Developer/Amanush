from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
import logging

from app.application.services.auth_service import AuthService
from app.application.services.jwt import JWTManager, get_jwt_manager
from app.application.services.file_service import FileService
from app.application.services.agent_service import AgentService
from app.application.errors.exceptions import (
    UnauthorizedError, ValidationError, NotFoundError, BadRequestError
)
from app.interfaces.dependencies import get_auth_service, get_current_user, get_file_service, get_agent_service
from app.interfaces.schemas.response import APIResponse, ResourceAccessTokenResponse
from app.interfaces.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest, RefreshTokenRequest,
    LoginResponse, RegisterResponse, AuthStatusResponse, RefreshTokenResponse,
    UserResponse
)
from app.interfaces.schemas.request import AccessTokenRequest
from app.core.config import get_settings
from app.domain.models.user import User
from app.domain.models.auth import AuthToken

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_response(user) -> UserResponse:
    """Convert user domain model to response schema"""
    return UserResponse(
        id=user.id,
        fullname=user.fullname,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at
    )


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[LoginResponse]:
    """User login endpoint"""
    # Authenticate user and get tokens
    auth_result = await auth_service.login_with_tokens(request.email, request.password)
    
    # Return success response with tokens
    return APIResponse.success(LoginResponse(
        user=_user_to_response(auth_result.user),
        access_token=auth_result.access_token,
        refresh_token=auth_result.refresh_token,
        token_type=auth_result.token_type
    ))


@router.post("/register", response_model=APIResponse[RegisterResponse])
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RegisterResponse]:
    """User registration endpoint"""
    # Register user
    user = await auth_service.register_user(
        fullname=request.fullname,
        password=request.password,
        email=request.email
    )
    
    # Generate tokens for the new user
    access_token = auth_service.jwt_manager.create_access_token(user)
    refresh_token = auth_service.jwt_manager.create_refresh_token(user)
    
    # Return success response with tokens
    return APIResponse.success(RegisterResponse(
        user=_user_to_response(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    ))


@router.get("/status", response_model=APIResponse[AuthStatusResponse])
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[AuthStatusResponse]:
    """Get authentication status and configuration"""
    settings = get_settings()
    
    return APIResponse.success(AuthStatusResponse(
        authenticated=False,  # This would be determined by middleware in real app
        user=None,
        auth_provider=settings.auth_provider
    ))


@router.post("/change-password", response_model=APIResponse[dict])
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Change user password endpoint"""
    # Change password for current user
    await auth_service.change_password(current_user.id, request.old_password, request.new_password)
    
    return APIResponse.success({})


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserResponse]:
    """Get current user information"""
    return APIResponse.success(_user_to_response(current_user))


@router.get("/user/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[UserResponse]:
    """Get user information by ID (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    return APIResponse.success(_user_to_response(user))


@router.post("/user/{user_id}/deactivate", response_model=APIResponse[dict])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Deactivate user account (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    # Prevent self-deactivation
    if current_user.id == user_id:
        raise BadRequestError("Cannot deactivate your own account")
    
    await auth_service.deactivate_user(user_id)
    return APIResponse.success({})


@router.post("/user/{user_id}/activate", response_model=APIResponse[dict])
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Activate user account (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    await auth_service.activate_user(user_id)
    return APIResponse.success({})


@router.post("/refresh", response_model=APIResponse[RefreshTokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RefreshTokenResponse]:
    """Refresh access token endpoint"""
    # Refresh access token
    token_result = await auth_service.refresh_access_token(request.refresh_token)
    
    return APIResponse.success(RefreshTokenResponse(
        access_token=token_result.access_token,
        token_type=token_result.token_type
    ))


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """User logout endpoint"""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Authentication required")
    
    token = auth_header.split(" ")[1]
    
    # Revoke token
    await auth_service.logout(token)
    
    return APIResponse.success({})


@router.post("/access-tokens", response_model=APIResponse[ResourceAccessTokenResponse])
async def create_access_token(
    request_data: AccessTokenRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    file_service: FileService = Depends(get_file_service),
    agent_service: AgentService = Depends(get_agent_service),
    jwt_manager: JWTManager = Depends(get_jwt_manager)
) -> APIResponse[ResourceAccessTokenResponse]:
    """Generate unified access token for various resource types
    
    Supports:
    - file: File download access
    - vnc: VNC WebSocket access
    """
    
    # Validate expiration time (max 24 hours)
    expire_minutes = request_data.expire_minutes
    if expire_minutes > 24 * 60:
        expire_minutes = 24 * 60
    
    # Validate resource based on type
    if request_data.resource_type == "file":
        # Check if file exists
        file_info = await file_service.get_file_info(request_data.resource_id)
        if not file_info:
            raise NotFoundError("File not found")
        
    elif request_data.resource_type == "vnc":
        # Check if session exists and belongs to user
        await agent_service.get_session(request_data.resource_id, current_user.id)
        
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported resource type: {request_data.resource_type}"
        )
    
    # Create resource access token
    access_token = jwt_manager.create_resource_access_token(
        resource_type=request_data.resource_type,
        resource_id=request_data.resource_id,
        user_id=current_user.id,
        expire_minutes=expire_minutes
    )
    
    logger.info(f"Created {request_data.resource_type} access token for user {current_user.id}, resource {request_data.resource_id}")
    
    return APIResponse.success(ResourceAccessTokenResponse(
        access_token=access_token,
        resource_type=request_data.resource_type,
        resource_id=request_data.resource_id,
        expires_in=expire_minutes * 60,  # Convert to seconds
    )) 