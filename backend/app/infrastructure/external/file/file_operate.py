import logging
from typing import Optional, BinaryIO, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.domain.external.file_operate import FileOperate
from app.infrastructure.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class FileOperationFactory:
    """
    Factory for creating file storage operation instances based on configuration.
    """

    @staticmethod
    async def create_storage() -> FileOperate:
        """
        Create a file storage operation instance according to the configured storage type.

        Returns:
            FileOperate: The file operation instance (e.g., MongoDBStorage).

        Raises:
            ValueError: If the storage type is not supported.
        """
        _settings = get_settings()
        if _settings.storage_type == "mongodb":
            return MongoDBStorage()
        else:
            raise ValueError(f"Unsupported storage type: {_settings.storage_type}")


class MongoDBStorage(FileOperate):
    """
    MongoDB GridFS-based file storage implementation.
    """

    def __init__(self):
        self._settings = get_settings()
        self._client = None
        self._fs = None

    async def initialize(self):
        """
        Initialize the MongoDB client and GridFS bucket.
        """
        if self._client is None:
            mongodb = get_mongodb()
            await mongodb.initialize()
            self._client = mongodb.client
            self._fs = AsyncIOMotorGridFSBucket(self._client[self._settings.mongodb_database])

    async def upload_file(self, file_data: BinaryIO,
                          filename: str,
                          content_type: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> dict:
        """
        Upload a file to MongoDB GridFS.

        Args:
            file_data (BinaryIO): The file data stream.
            filename (str): The name of the file.
            content_type (str, optional): The MIME type of the file.
            metadata (dict, optional): Additional metadata for the file.

        Returns:
            dict: Information about the uploaded file, including filename, content_type, storage_type, storage_url, and file_size.

        Raises:
            ValueError: If the file size exceeds the configured limit.
        """
        if self._fs is None:
            await self.initialize()
        try:
            file_data.seek(0)
        except Exception:
            pass
        content = file_data.read()
        if len(content) > self._settings.max_file_size:
            raise ValueError("File size exceeds configured limit of", {self._settings.max_file_size})
        file_id = await self._fs.upload_from_stream(
            filename, content,
            metadata={"content_type": content_type}
        )
        return {
            "filename": filename,
            "content_type": content_type,
            "storage_type": "mongodb",
            "storage_url": str(file_id),
            "file_size": len(content),
        }

    async def download_file(self, storage_url: str) -> Optional[dict]:
        """
        Download a file from MongoDB GridFS.

        Args:
            storage_url (str): The storage URL or object ID of the file.

        Returns:
            dict: Information about the downloaded file, including content, filename, content_type, file_size, and metadata.
        """
        if self._fs is None:
            await self.initialize()

        grid_out = await self._fs.open_download_stream(ObjectId(storage_url))
        content = await grid_out.read()
        metadata = grid_out.metadata or {}
        return {
            'content': content,
            'filename': grid_out.filename,
            'content_type': metadata.get('content_type', 'application/octet-stream'),
            'file_size': len(content),
            'metadata': metadata
        }

    async def delete_file(self, storage_url: str) -> bool:
        """
        Delete a file from MongoDB GridFS.

        Args:
            storage_url (str): The storage URL or object ID of the file.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            await self._fs.delete(ObjectId(storage_url))
            await self._fs.chunks.delete_many({"files_id": ObjectId(storage_url)})
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
