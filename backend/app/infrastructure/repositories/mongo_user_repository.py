from typing import Optional, List
from datetime import datetime, timezone
import uuid
from app.domain.repositories.user_repository import UserRepository
from app.domain.models.user import User
from app.infrastructure.models.documents import UserDocument


class MongoUserRepository(UserRepository):
    """MongoDB implementation of UserRepository"""

    def _to_domain(self, document: UserDocument) -> User:
        """Convert MongoDB document to domain model"""
        return User(
            id=document.user_id,
            username=document.username,
            email=document.email,
            hashed_password=document.hashed_password,
            auth_type=document.auth_type,
            full_name=document.full_name,
            created_at=document.created_at,
            updated_at=document.updated_at,
            last_login_at=document.last_login_at,
        )

    def _to_document(self, user: User) -> UserDocument:
        """Convert domain model to MongoDB document"""
        return UserDocument(
            user_id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            auth_type=user.auth_type,
            full_name=user.full_name,
            created_at=user.created_at or datetime.now(timezone.utc),
            updated_at=user.updated_at or datetime.now(timezone.utc),
            last_login_at=user.last_login_at,
        )

    async def create(self, user: User) -> User:
        """Create a new user"""
        if not user.id:
            user.id = str(uuid.uuid4())
        
        if not user.created_at:
            user.created_at = datetime.now(timezone.utc)
        
        if not user.updated_at:
            user.updated_at = datetime.now(timezone.utc)

        document = self._to_document(user)
        await document.save()
        return self._to_domain(document)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        document = await UserDocument.find_one(UserDocument.user_id == user_id)
        return self._to_domain(document) if document else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        document = await UserDocument.find_one(UserDocument.username == username)
        return self._to_domain(document) if document else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        document = await UserDocument.find_one(UserDocument.email == email)
        return self._to_domain(document) if document else None

    async def update(self, user: User) -> User:
        """Update user information"""
        user.updated_at = datetime.now(timezone.utc)
        
        document = await UserDocument.find_one(UserDocument.user_id == user.id)
        if not document:
            raise ValueError(f"User with id {user.id} not found")

        # Update fields
        document.username = user.username
        document.email = user.email
        document.hashed_password = user.hashed_password
        document.full_name = user.full_name
        document.updated_at = user.updated_at
        document.last_login_at = user.last_login_at

        await document.save()
        return self._to_domain(document)

    async def delete(self, user_id: str) -> bool:
        """Delete user by ID"""
        result = await UserDocument.find_one(UserDocument.user_id == user_id).delete()
        return result is not None

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        documents = await UserDocument.find().skip(skip).limit(limit).to_list()
        return [self._to_domain(doc) for doc in documents]

    async def count(self) -> int:
        """Count total users"""
        return await UserDocument.count() 