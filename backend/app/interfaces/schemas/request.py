from pydantic import BaseModel
from typing import Optional, List


class FileViewRequest(BaseModel):
    file: str


class ShellViewRequest(BaseModel):
    session_id: str


class AttachmentBindRequest(BaseModel):
    filename: str
    content_type: str
    file_size: int
    storage_type: str
    storage_url: str


class ChatRequest(BaseModel):
    timestamp: Optional[int] = None
    message: Optional[str] = None
    event_id: Optional[str] = None
    attachments: Optional[List[AttachmentBindRequest]] = None
