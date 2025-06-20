from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.domain.models.user import User
from app.application.services.user_service import UserService
from app.infrastructure.external.auth.jwt_auth import JWTAuth
from app.infrastructure.repositories.mongo_user_repository import MongoUserRepository


security = HTTPBearer()


def get_jwt_auth() -> JWTAuth:
    """Get JWT auth instance"""
    return JWTAuth()


def get_user_repository() -> MongoUserRepository:
    """Get user repository instance"""
    return MongoUserRepository()


def get_user_service() -> UserService:
    """Get user service instance"""
    return UserService(
        user_repository=get_user_repository(),
        jwt_auth=get_jwt_auth()
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_service: UserService = Depends(get_user_service)
) -> Optional[User]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    user = await user_service.verify_token(token)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Get current user from JWT token (required)"""
    token = credentials.credentials
    user = await user_service.verify_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    
    return user


 