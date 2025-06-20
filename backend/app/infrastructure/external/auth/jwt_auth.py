from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.infrastructure.config import get_settings


class JWTAuth:
    """JWT Authentication service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # Refresh tokens expire in 7 days by default
            expire = datetime.now(timezone.utc) + timedelta(days=7)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.settings.jwt_secret_key, algorithm=self.settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.settings.jwt_secret_key, algorithms=[self.settings.jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT refresh token"""
        payload = self.verify_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None 