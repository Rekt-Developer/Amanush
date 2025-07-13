import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.domain.models.user import User, UserRole
from app.domain.repositories.user_repository import UserRepository
from app.application.errors.exceptions import UnauthorizedError, ValidationError
from app.infrastructure.config import get_settings
from app.infrastructure.utils.jwt import get_jwt_manager
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service handling user authentication and authorization"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.settings = get_settings()
        self.jwt_manager = get_jwt_manager()
    
    def _hash_password(self, password: str, salt: str = None) -> str:
        """Hash password using configured algorithm"""
        if salt is None:
            salt = self.settings.password_salt or secrets.token_hex(32)
        
        # Support for different hash algorithms
        if self.settings.password_hash_algorithm == "pbkdf2_sha256":
            return self._pbkdf2_sha256(password, salt)
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.settings.password_hash_algorithm}")
    
    def _pbkdf2_sha256(self, password: str, salt: str) -> str:
        """PBKDF2 with SHA-256 implementation"""
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Use configured rounds
        rounds = self.settings.password_hash_rounds
        
        # Generate hash
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, rounds)
        
        # Return salt + hash as hex string
        return salt + hash_bytes.hex()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            # Extract salt from stored hash
            salt_length = len(self.settings.password_salt or secrets.token_hex(32))
            salt = hashed_password[:salt_length]
            
            # Hash the provided password with the same salt
            new_hash = self._hash_password(password, salt)
            
            # Compare hashes
            return new_hash == hashed_password
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def _generate_user_id(self) -> str:
        """Generate unique user ID"""
        return f"user_{secrets.token_hex(16)}"
    
    async def register_user(self, username: str, password: str, email: str = None, role: UserRole = UserRole.USER) -> User:
        """Register a new user"""
        logger.info(f"Registering new user: {username}")
        
        # Check if authentication is disabled
        if self.settings.auth_provider == "none":
            raise ValidationError("User registration is disabled when auth_provider is 'none'")
        
        # Validate input
        if not username or len(username.strip()) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        
        if not password or len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long")
        
        # Check if user already exists
        if await self.user_repository.user_exists(username):
            raise ValidationError(f"User {username} already exists")
        
        if email and await self.user_repository.email_exists(email):
            raise ValidationError(f"Email {email} already exists")
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
        user = User(
            id=self._generate_user_id(),
            username=username.strip(),
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        created_user = await self.user_repository.create_user(user)
        
        logger.info(f"User registered successfully: {created_user.id}")
        return created_user
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password"""
        logger.debug(f"Authenticating user: {username}")
        
        # Handle different auth providers
        if self.settings.auth_provider == "none":
            # No authentication required - return a default user
            return User(
                id="anonymous",
                username="anonymous",
                role=UserRole.USER,
                is_active=True
            )
        
        elif self.settings.auth_provider == "local":
            # Local authentication using configured credentials
            if (username == self.settings.local_auth_username and 
                password == self.settings.local_auth_password):
                return User(
                    id="local_admin",
                    username=self.settings.local_auth_username,
                    role=UserRole.ADMIN,
                    is_active=True
                )
            else:
                logger.warning(f"Local authentication failed for user: {username}")
                return None
        
        elif self.settings.auth_provider == "password":
            # Database password authentication
            user = await self.user_repository.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"User account is inactive: {username}")
                return None
            
            if not user.password_hash:
                logger.warning(f"User has no password hash: {username}")
                return None
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            user.update_last_login()
            await self.user_repository.update_user(user)
            
            logger.info(f"User authenticated successfully: {username}")
            return user
        
        else:
            raise ValueError(f"Unsupported auth provider: {self.settings.auth_provider}")
    
    async def login_with_tokens(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return JWT tokens"""
        user = await self.authenticate_user(username, password)
        
        if not user:
            raise UnauthorizedError("Invalid username or password")
        
        # Generate JWT tokens
        access_token = self.jwt_manager.create_access_token(user)
        refresh_token = self.jwt_manager.create_refresh_token(user)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        payload = self.jwt_manager.verify_token(refresh_token)
        
        if not payload:
            raise UnauthorizedError("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        
        # Get user from database
        user_id = payload.get("sub")
        user = await self.user_repository.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        
        # Generate new access token
        new_access_token = self.jwt_manager.create_access_token(user)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user"""
        user_info = self.jwt_manager.get_user_from_token(token)
        
        if not user_info:
            return None
        
        # For database users, verify user still exists and is active
        if self.settings.auth_provider == "password":
            user = await self.user_repository.get_user_by_id(user_info["id"])
            if not user or not user.is_active:
                return None
            return user
        
        # For local/none authentication, create user from token info
        return User(
            id=user_info["id"],
            username=user_info["username"],
            email=user_info.get("email"),
            role=UserRole(user_info.get("role", "user")),
            is_active=user_info.get("is_active", True)
        )
    
    async def logout(self, token: str) -> bool:
        """Logout user by revoking token"""
        return self.jwt_manager.revoke_token(token)
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repository.get_user_by_id(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.user_repository.get_user_by_username(username)
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        logger.info(f"Changing password for user: {user_id}")
        
        # Only supported for password authentication
        if self.settings.auth_provider != "password":
            raise ValidationError("Password change is only supported for password authentication")
        
        # Get user
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValidationError("User not found")
        
        # Verify old password
        if not self._verify_password(old_password, user.password_hash):
            raise UnauthorizedError("Invalid current password")
        
        # Validate new password
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters long")
        
        # Hash new password
        user.password_hash = self._hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # Save changes
        await self.user_repository.update_user(user)
        
        logger.info(f"Password changed successfully for user: {user_id}")
        return True
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        logger.info(f"Deactivating user: {user_id}")
        
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValidationError("User not found")
        
        user.deactivate()
        await self.user_repository.update_user(user)
        
        logger.info(f"User deactivated successfully: {user_id}")
        return True
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account"""
        logger.info(f"Activating user: {user_id}")
        
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValidationError("User not found")
        
        user.activate()
        await self.user_repository.update_user(user)
        
        logger.info(f"User activated successfully: {user_id}")
        return True 