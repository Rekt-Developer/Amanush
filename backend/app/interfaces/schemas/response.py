from typing import Any, Generic, Optional, TypeVar, List
from datetime import datetime
from pydantic import BaseModel
from app.interfaces.schemas.event import AgentSSEEvent
from app.domain.models.session import SessionStatus

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: Optional[T] = None

    @staticmethod
    def success(data: Optional[T] = None) -> "APIResponse[T]":
        return APIResponse(code=0, msg="success", data=data)

    @staticmethod
    def error(code: int, msg: str) -> "APIResponse[T]":
        return APIResponse(code=code, msg=msg, data=None)


class CreateSessionResponse(BaseModel):
    session_id: str


class GetSessionResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    events: List[AgentSSEEvent] = []


class ListSessionItem(BaseModel):
    session_id: str
    title: Optional[str] = None
    latest_message: Optional[str] = None
    latest_message_at: Optional[int] = None
    status: SessionStatus
    unread_message_count: int


class ListSessionResponse(BaseModel):
    sessions: List[ListSessionItem]


class ConsoleRecord(BaseModel):
    ps1: str
    command: str
    output: str


class ShellViewResponse(BaseModel):
    output: str
    session_id: str
    console: Optional[List[ConsoleRecord]] = None


class FileViewResponse(BaseModel):
    content: str
    file: str


class AttachmentUploadResponse(BaseModel):
    """
    Response model for file upload result.

    Fields:
        filename (str): The name of the uploaded file.
        content_type (str): The MIME type of the file.
        file_size (int): The size of the file in bytes.
        storage_type (str): The type of storage backend (e.g., 'mongodb').
        storage_url (str): The storage URL or object ID in the backend.
    """
    filename: str
    content_type: str
    file_size: int
    storage_type: str
    storage_url: str


class AttachmentDownloadResponse(BaseModel):
    """
    Response model for file download result.

    Fields:
        storage_url (str): The storage URL or object ID in the backend.
        filename (str): The name of the downloaded file.
        content_type (str): The MIME type of the file.
        content (str): The file content, base64 encoded.
        file_size (int): The size of the file in bytes.
    """
    storage_url: str
    filename: str
    content_type: str
    content: str
    file_size: int


class SessionAttachmentsResponse(BaseModel):
    session_id: str
    attachments: List[dict]
