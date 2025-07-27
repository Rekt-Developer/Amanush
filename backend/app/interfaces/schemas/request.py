from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    timestamp: Optional[int] = None
    message: Optional[str] = None
    attachments: Optional[List[str]] = None
    event_id: Optional[str] = None

class FileViewRequest(BaseModel):
    file: str

class ShellViewRequest(BaseModel):
    session_id: str

class AccessTokenRequest(BaseModel):
    resource_type: str = Field(..., description="Type of resource (file, vnc, etc.)")
    resource_id: str = Field(..., description="ID of the resource")
    expire_minutes: int = Field(60, description="Token expiration time in minutes (max 24 hours)", ge=1, le=24*60)
