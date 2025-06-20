from typing import Optional, List
from datetime import datetime, timezone
from app.domain.models.user import User, AuthType
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.external.auth.jwt_auth import JWTAuth
from app.application.errors.exceptions import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError


class UserService:
    """User application service"""
    
    def __init__(self, user_repository: UserRepository, jwt_auth: JWTAuth):
        self.user_repository = user_repository
        self.jwt_auth = jwt_auth
    
    async def register_user(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> User:
        """Register a new user"""
        # Check if username already exists
        existing_user = await self.user_repository.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsError(f"Username '{username}' already exists")
        
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsError(f"Email '{email}' already exists")
        
        # Hash password
        hashed_password = self.jwt_auth.get_password_hash(password)
        
        # Create user
        user = User(
            id="",  # Will be generated in repository
            username=username,
            email=email,
            hashed_password=hashed_password,
            auth_type=AuthType.PASSWORD,
            full_name=full_name,
        )
        
        return await self.user_repository.create(user)
    
    async def create_temporary_user(self) -> tuple[str, str, User]:
        """Create a temporary user and return access token and refresh token"""
        import uuid
        import secrets
        
        # Generate unique username and email for temporary user
        temp_id = str(uuid.uuid4())[:8]
        username = f"temp_{temp_id}"
        email = f"temp_{temp_id}@temporary.local"
        
        # Generate a random password (not used for authentication)
        temp_password = secrets.token_urlsafe(32)
        hashed_password = self.jwt_auth.get_password_hash(temp_password)
        
        # Create temporary user
        user = User(
            id="",  # Will be generated in repository
            username=username,
            email=email,
            hashed_password=hashed_password,
            auth_type=AuthType.TEMPORARY,
            full_name=f"Temporary User {temp_id}",
        )
        
        created_user = await self.user_repository.create(user)
        
        # Create tokens for temporary user
        token_data = {"sub": created_user.id, "username": created_user.username, "auth_type": created_user.auth_type.value}
        access_token = self.jwt_auth.create_access_token(data=token_data)
        refresh_token = self.jwt_auth.create_refresh_token(data=token_data)
        
        return access_token, refresh_token, created_user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = await self.user_repository.get_by_username(username)
        if not user:
            return None
        

        
        if not self.jwt_auth.verify_password(password, user.hashed_password):
            return None
        
        # Update last login time
        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repository.update(user)
        
        return user
    
    async def login(self, username: str, password: str) -> tuple[str, str, User]:
        """Login user and return access token and refresh token"""
        user = await self.authenticate_user(username, password)
        if not user:
            raise InvalidCredentialsError("Invalid username or password")
        
        # Create tokens
        token_data = {"sub": user.id, "username": user.username, "auth_type": user.auth_type.value}
        access_token = self.jwt_auth.create_access_token(data=token_data)
        refresh_token = self.jwt_auth.create_refresh_token(data=token_data)
        
        return access_token, refresh_token, user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repository.get_by_id(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.user_repository.get_by_username(username)
    
    async def update_user(self, user_id: str, **kwargs) -> User:
        """Update user information"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id '{user_id}' not found")
        
        # Update allowed fields
        if 'username' in kwargs:
            # Check if new username already exists
            existing_user = await self.user_repository.get_by_username(kwargs['username'])
            if existing_user and existing_user.id != user_id:
                raise UserAlreadyExistsError(f"Username '{kwargs['username']}' already exists")
            user.username = kwargs['username']
        
        if 'email' in kwargs:
            # Check if new email already exists
            existing_user = await self.user_repository.get_by_email(kwargs['email'])
            if existing_user and existing_user.id != user_id:
                raise UserAlreadyExistsError(f"Email '{kwargs['email']}' already exists")
            user.email = kwargs['email']
        
        if 'full_name' in kwargs:
            user.full_name = kwargs['full_name']
        
        if 'password' in kwargs:
            user.hashed_password = self.jwt_auth.get_password_hash(kwargs['password'])
        

        

        
        return await self.user_repository.update(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id '{user_id}' not found")
        
        return await self.user_repository.delete(user_id)
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        return await self.user_repository.list_users(skip=skip, limit=limit)
    
    async def count_users(self) -> int:
        """Count total users"""
        return await self.user_repository.count()
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user"""
        user_id = self.jwt_auth.get_user_id_from_token(token)
        if not user_id:
            return None
        
        return await self.user_repository.get_by_id(user_id)
    
    async def refresh_token(self, refresh_token: str) -> tuple[str, str, User]:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = self.jwt_auth.verify_refresh_token(refresh_token)
        if not payload:
            raise InvalidCredentialsError("Invalid refresh token")
        
        # Get user from token
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsError("Invalid refresh token")
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        # Create new tokens
        token_data = {"sub": user.id, "username": user.username, "auth_type": user.auth_type.value}
        new_access_token = self.jwt_auth.create_access_token(data=token_data)
        new_refresh_token = self.jwt_auth.create_refresh_token(data=token_data)
        
        return new_access_token, new_refresh_token, user 