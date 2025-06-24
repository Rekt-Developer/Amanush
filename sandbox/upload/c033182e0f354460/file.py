from quopri import quote
from typing import Optional, Dict, Any

import httpx

from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class FileTool(BaseTool):
    """File tool class, providing file operation functions"""

    name: str = "file"

    def __init__(self, sandbox: Sandbox):
        """Initialize file tool class

        Args:
            sandbox: Sandbox service
        """
        super().__init__()
        self.sandbox = sandbox

    @tool(
        name="file_read",
        description="Read file content. Use for checking file contents, analyzing logs, or reading configuration files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to read"
            },
            "start_line": {
                "type": "integer",
                "description": "(Optional) Starting line to read from, 0-based"
            },
            "end_line": {
                "type": "integer",
                "description": "(Optional) Ending line number (exclusive)"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file"]
    )
    async def file_read(
        self,
        file: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Read file content

        Args:
            file: Absolute path of the file to read
            start_line: (Optional) Starting line, 0-based
            end_line: (Optional) Ending line (exclusive)
            sudo: (Optional) Whether to use sudo privileges

        Returns:
            File content
        """
        # Directly call sandbox's file_read method
        return await self.sandbox.file_read(
            file=file,
            start_line=start_line,
            end_line=end_line,
            sudo=sudo
        )

    @tool(
        name="file_write",
        description="Overwrite or append content to a file. Use for creating new files, appending content, or modifying existing files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to write to"
            },
            "content": {
                "type": "string",
                "description": "Text content to write"
            },
            "append": {
                "type": "boolean",
                "description": "(Optional) Whether to use append mode"
            },
            "leading_newline": {
                "type": "boolean",
                "description": "(Optional) Whether to add a leading newline"
            },
            "trailing_newline": {
                "type": "boolean",
                "description": "(Optional) Whether to add a trailing newline"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "content"]
    )
    async def file_write(
        self,
        file: str,
        content: str,
        append: Optional[bool] = False,
        leading_newline: Optional[bool] = False,
        trailing_newline: Optional[bool] = False,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Write content to file

        Args:
            file: Absolute path of the file to write to
            content: Text content to write
            append: (Optional) Whether to use append mode
            leading_newline: (Optional) Whether to add a leading newline
            trailing_newline: (Optional) Whether to add a trailing newline
            sudo: (Optional) Whether to use sudo privileges

        Returns:
            Write result
        """
        # Prepare content
        final_content = content
        if leading_newline:
            final_content = "\n" + final_content
        if trailing_newline:
            final_content = final_content + "\n"

        # Directly call sandbox's file_write method, pass all parameters
        return await self.sandbox.file_write(
            file=file,
            content=final_content,
            append=append,
            leading_newline=False,  # Already handled in final_content
            trailing_newline=False,  # Already handled in final_content
            sudo=sudo
        )

    @tool(
        name="file_str_replace",
        description="Replace specified string in a file. Use for updating specific content in files or fixing errors in code.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to perform replacement on"
            },
            "old_str": {
                "type": "string",
                "description": "Original string to be replaced"
            },
            "new_str": {
                "type": "string",
                "description": "New string to replace with"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "old_str", "new_str"]
    )
    async def file_str_replace(
        self,
        file: str,
        old_str: str,
        new_str: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Replace specified string in file

        Args:
            file: Absolute path of the file to perform replacement on
            old_str: Original string to be replaced
            new_str: New string to replace with
            sudo: (Optional) Whether to use sudo privileges

        Returns:
            Replacement result
        """
        # Directly call sandbox's file_replace method
        return await self.sandbox.file_replace(
            file=file,
            old_str=old_str,
            new_str=new_str,
            sudo=sudo
        )

    @tool(
        name="file_find_in_content",
        description="Search for matching text within file content. Use for finding specific content or patterns in files.",
        parameters={
            "file": {
                "type": "string",
                "description": "Absolute path of the file to search within"
            },
            "regex": {
                "type": "string",
                "description": "Regular expression pattern to match"
            },
            "sudo": {
                "type": "boolean",
                "description": "(Optional) Whether to use sudo privileges"
            }
        },
        required=["file", "regex"]
    )
    async def file_find_in_content(
        self,
        file: str,
        regex: str,
        sudo: Optional[bool] = False
    ) -> ToolResult:
        """Search for matching text in file content

        Args:
            file: Absolute path of the file to search
            regex: Regular expression pattern for matching
            sudo: (Optional) Whether to use sudo privileges

        Returns:
            Search results
        """
        # Directly call sandbox's file_search method
        return await self.sandbox.file_search(
            file=file,
            regex=regex,
            sudo=sudo
        )

    @tool(
        name="file_find_by_name",
        description="Find files by name pattern in specified directory. Use for locating files with specific naming patterns.",
        parameters={
            "path": {
                "type": "string",
                "description": "Absolute path of directory to search"
            },
            "glob": {
                "type": "string",
                "description": "Filename pattern using glob syntax wildcards"
            }
        },
        required=["path", "glob"]
    )
    async def file_find_by_name(
        self,
        path: str,
        glob: str
    ) -> ToolResult:
        """Find files by name pattern in specified directory

        Args:
            path: Absolute path of directory to search
            glob: Filename pattern using glob syntax wildcards

        Returns:
            Search results
        """
        # Directly call sandbox's file_find method
        return await self.sandbox.file_find(
            path=path,
            glob_pattern=glob
        )

    @tool(
        name="file_upload_to_sandbox",
        description="Upload a text file to the sandbox. The file will be saved in the sandbox's default upload location.",
        parameters={
            "filename": {
                "type": "string",
                "description": "The name of the file to be created in the sandbox."
            },
            "content": {
                "type": "string",
                "description": "The text content to write into the file."
            }
        },
        required=["filename", "content"]
    )
    async def file_upload_to_sandbox(
            self,
            filename: str,
            content: str
    ) -> ToolResult:
        """
        Uploads a text file to the sandbox by calling its HTTP API.

        Args:
            filename: The name for the file.
            content: The text content of the file.

        Returns:
            A ToolResult indicating success or failure.
        """
        try:
            # NOTE: Assumes the sandbox URL can be retrieved or is configured elsewhere.
            # Using localhost as a placeholder.
            sandbox_url = getattr(self.sandbox, 'base_url', 'http://localhost:8000')
            upload_url = f"{sandbox_url}/api/v1/file/upload"

            file_content = content.encode('utf-8')
            files = {'file_data': (filename, file_content, 'text/plain')}

            async with httpx.AsyncClient() as client:
                response = await client.post(upload_url, files=files)
                response.raise_for_status()
                response_data = response.json()

                return ToolResult(
                    success=response_data.get('success', False),
                    message=response_data.get('message'),
                    data=response_data.get('data')
                )
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False,
                              message=f"HTTP error during file upload: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to upload file: {str(e)}")

    @tool(
        name="file_download_from_sandbox",
        description="Download a file from the sandbox and return its content as text.",
        parameters={
            "file_path": {
                "type": "string",
                "description": "The absolute path of the file to download from the sandbox."
            }
        },
        required=["file_path"]
    )
    async def file_download_from_sandbox(
            self,
            file_path: str
    ) -> ToolResult:
        """
        Downloads a file from the sandbox by calling its HTTP API.

        Args:
            file_path: The absolute path of the file to download.

        Returns:
            A ToolResult containing the file's text content.
        """
        try:
            sandbox_url = getattr(self.sandbox, 'base_url', 'http://localhost:8000')
            encoded_path = quote(file_path)
            download_url = f"{sandbox_url}/api/v1/file/download?file_path={encoded_path}"

            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                response.raise_for_status()

                return ToolResult(
                    success=True,
                    message="File downloaded successfully.",
                    data={"content": response.text}
                )
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False,
                              message=f"HTTP error during file download: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to download file: {str(e)}")


    @tool(
        name="file_upload_to_backend",
        description="Upload a file to the application's internal datastore (MongoDB). Use this for permanent storage of files.",
        parameters={
            "filename": {
                "type": "string",
                "description": "The name of the file to be uploaded."
            },
            "content": {
                "type": "string",
                "description": "The text content of the file."
            }
        },
        required=["filename", "content"]
    )
    async def file_upload_to_backend(
            self,
            filename: str,
            content: str
    ) -> ToolResult:
        """
        Uploads a file to the backend's attachment endpoint.

        Args:
            filename: The name for the file.
            content: The text content of the file.

        Returns:
            A ToolResult indicating success or failure.
        """
        try:
            backend_url = getattr(self.sandbox, 'backend_base_url', 'http://localhost:8000')
            upload_url = f"{backend_url}/attachments/upload"

            file_content = content.encode('utf-8')
            files = {'file': (filename, file_content, 'text/plain')}

            async with httpx.AsyncClient() as client:
                response = await client.post(upload_url, files=files)
                response.raise_for_status()
                response_data = response.json()

                return ToolResult(
                    success=response_data.get('success', False),
                    message=response_data.get('message', 'Upload completed.'),
                    data=response_data.get('data')
                )
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False,
                              message=f"HTTP error during attachment upload: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to upload attachment: {str(e)}")


    @tool(
        name="file_download_from_backend",
        description="Download a file from the application's internal datastore (MongoDB). Use this to retrieve previously uploaded files.",
        parameters={
            "storage_url": {
                "type": "string",
                "description": "The storage URL of the file to download (obtained from upload response or session attachments)."
            }
        },
        required=["storage_url"]
    )
    async def file_download_from_backend(
            self,
            storage_url: str
    ) -> ToolResult:
        """
        Downloads a file from the backend's attachment endpoint.

        Args:
            storage_url: The storage URL of the file to download.

        Returns:
            A ToolResult containing the file's content and metadata.
        """
        try:
            backend_url = getattr(self.sandbox, 'backend_base_url', 'http://localhost:8000')
            download_url = f"{backend_url}/attachments/download/{storage_url}"

            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                response.raise_for_status()

                # Get filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                filename = None
                if 'filename=' in content_disposition:
                    # Extract filename from Content-Disposition header
                    import re
                    filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)

                return ToolResult(
                    success=True,
                    message="File downloaded successfully.",
                    data={
                        "content": response.text,
                        "filename": filename,
                        "content_type": response.headers.get('Content-Type'),
                        "content_length": response.headers.get('Content-Length')
                    }
                )
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False,
                              message=f"HTTP error during attachment download: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to download attachment: {str(e)}")