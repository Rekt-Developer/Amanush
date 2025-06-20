import base64
import logging

from typing import List
from bson import ObjectId
from fastapi import UploadFile

from app.infrastructure.models.documents import AttachmentDocument
from app.infrastructure.repositories.mongo_attachment_repository import AttachmentRepository
from app.infrastructure.external.file.file_operate import FileOperationFactory
from app.interfaces.schemas.response import AttachmentUploadResponse, AttachmentDownloadResponse

# Set up logger
logger = logging.getLogger(__name__)


class AttachmentService:
    """
    Service for handling file attachments, including upload, download, binding to sessions, and deletion.
    """

    def __init__(self, storage_factory: FileOperationFactory, attachment_repository: AttachmentRepository):
        self.storage_factory = storage_factory
        self.repository = attachment_repository

    async def upload_attachment(self, file: UploadFile) -> AttachmentUploadResponse:
        """
        Upload a file attachment to the storage backend.

        Args:
            file (UploadFile): The file to be uploaded.

        Returns:
            AttachmentUploadResponse: The upload result, including file info and storage URL.

        Raises:
            Exception: If upload fails or storage backend is unavailable.
        """
        storage = await self.storage_factory.create_storage()
        upload_result = await storage.upload_file(file.file, file.filename, file.content_type)
        return AttachmentUploadResponse(**upload_result)

    async def download_attachment(self, storage_url: str) -> AttachmentDownloadResponse:
        """
        Download an attachment from the storage backend.

        Args:
            storage_url (str): The storage URL or object ID of the file in GridFS.

        Returns:
            AttachmentDownloadResponse: The download result, including file content and metadata.

        Raises:
            Exception: If download fails or file does not exist.
        """
        storage = await self.storage_factory.create_storage()
        result = await storage.download_file(storage_url)

        return AttachmentDownloadResponse(
            storage_url=storage_url,
            filename=result['filename'],
            content_type=result['content_type'],
            content=result['content'],
            file_size=result['file_size']
        )

    async def bind_attachment_to_session(self, session_id: str,
                                         filename: str, content_type: str, file_size: int,
                                         storage_type: str, storage_url: str) -> AttachmentDocument:
        """
        Bind an attachment to a session (called when creating a session).

        Args:
            session_id (str): The session ID.
            filename (str): The name of the file.
            content_type (str): The MIME type of the file.
            file_size (int): The size of the file in bytes.
            storage_type (str): The type of storage backend.
            storage_url (str): The storage URL or object ID.

        Returns:
            AttachmentDocument: The saved attachment document.
        """
        # 创建AttachmentDocument
        attachment = AttachmentDocument(
            attachment_id=str(ObjectId()),
            session_id=session_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            storage_type=storage_type,
            storage_url=storage_url
        )

        return await self.repository.save(attachment)

    async def delete_attachment(self, _id: str) -> None:
        """
        Delete an attachment from both storage and database.

        Args:
            _id (str): The unique ID of the attachment document.
        """
        attachment = await self.repository.find_by_id(_id)
        if not attachment:
            return

        storage = await self.storage_factory.create_storage()
        await storage.delete_file(attachment.storage_url)
        await self.repository.delete(attachment.attachment_id)

    async def get_session_attachments(self, session_id: str) -> List[AttachmentDocument]:
        """
        Get all attachments for a given session.

        Args:
            session_id (str): The session ID.

        Returns:
            List[AttachmentDocument]: List of attachment documents for the session.
        """
        return await self.repository.find_by_session_id(session_id)

    async def get_attachments_by_session(self, session_id: str) -> List[AttachmentDocument]:
        """
        Get all attachments for a given session (alias for get_session_attachments).

        Args:
            session_id (str): The session ID.

        Returns:
            List[AttachmentDocument]: List of attachment documents for the session.
        """
        return await self.repository.find_by_session_id(session_id)
