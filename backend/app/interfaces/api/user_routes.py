from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from app.domain.models.user import User
from app.application.services.user_service import UserService
from app.infrastructure.middleware.auth import get_current_user, get_user_service
from app.interfaces.schemas.user import (
    UserRegisterRequest, UserLoginRequest, UserUpdateRequest, RefreshTokenRequest,
    UserResponse, LoginResponse, UserListResponse, TemporaryUserResponse, RefreshTokenResponse
)
from app.interfaces.schemas.response import APIResponse


router = APIRouter(prefix="/users", tags=["users"])


def user_to_response(user: User) -> UserResponse:
    """Convert User domain model to UserResponse"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        auth_type=user.auth_type,
        full_name=user.full_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.post("/register", response_model=APIResponse[UserResponse])
async def register_user(
    request: UserRegisterRequest,
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[UserResponse]:
    """Register a new user"""
    user = await user_service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    return APIResponse.success(user_to_response(user))


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login_user(
    request: UserLoginRequest,
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[LoginResponse]:
    """User login"""
    access_token, refresh_token, user = await user_service.login(
        username=request.username,
        password=request.password
    )
    
    response = LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_to_response(user)
    )
    return APIResponse.success(response)


@router.post("/temporary", response_model=APIResponse[TemporaryUserResponse])
async def create_temporary_user(
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[TemporaryUserResponse]:
    """Create a temporary user"""
    access_token, refresh_token, user = await user_service.create_temporary_user()
    
    response = TemporaryUserResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_to_response(user)
    )
    return APIResponse.success(response)


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserResponse]:
    """Get current user information"""
    return APIResponse.success(user_to_response(current_user))


@router.put("/me", response_model=APIResponse[UserResponse])
async def update_current_user(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[UserResponse]:
    """Update current user information"""
    update_data = request.model_dump(exclude_unset=True)
    user = await user_service.update_user(current_user.id, **update_data)
    return APIResponse.success(user_to_response(user))


@router.post("/refresh", response_model=APIResponse[RefreshTokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[RefreshTokenResponse]:
    """Refresh access token using refresh token"""
    access_token, refresh_token, user = await user_service.refresh_token(request.refresh_token)
    
    response = RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_to_response(user)
    )
    return APIResponse.success(response)


@router.get("/{user_id}", response_model=APIResponse[UserResponse])
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
) -> APIResponse[UserResponse]:
    """Get user by ID (requires authentication)"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return APIResponse.success(user_to_response(user))