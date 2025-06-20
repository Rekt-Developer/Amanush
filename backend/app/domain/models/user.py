from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class AuthType(str, Enum):
    PASSWORD = "password"      # Username/password authentication
    TEMPORARY = "temporary"    # Temporary user (system generated, no authentication required)


@dataclass
class User:
    id: str
    username: str
    email: str
    hashed_password: str
    auth_type: AuthType = AuthType.PASSWORD
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    def is_temporary(self) -> bool:
        """Check if user is temporary"""
        return self.auth_type == AuthType.TEMPORARY

 