from typing import Protocol, Optional, BinaryIO, Dict, Any



class FileOperate(Protocol):

    async def upload_file(self,
                          file_data: BinaryIO,
                          filename: str,
                          content_type: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> dict:
        ...

    async def download_file(self, storage_url: str) ->  Optional[dict]:
        ...

    async def delete_file(self, storage_url: str) -> bool:
        ...
