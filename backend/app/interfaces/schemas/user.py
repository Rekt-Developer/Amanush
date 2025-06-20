from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.domain.models.user import AuthType


# Request schemas
class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str





# Response schemas
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    auth_type: AuthType
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TemporaryUserResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int
    skip: int
    limit: int 