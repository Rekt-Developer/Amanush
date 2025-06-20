from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models.user import User


class UserRepository(ABC):
    """Abstract user repository interface"""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user information"""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total users"""
        pass 