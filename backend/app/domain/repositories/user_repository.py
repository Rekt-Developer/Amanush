from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.user import User


class UserRepository(ABC):
    """User repository interface"""
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update user information"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        pass
    
    @abstractmethod
    async def user_exists(self, username: str) -> bool:
        """Check if user exists by username"""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        pass 