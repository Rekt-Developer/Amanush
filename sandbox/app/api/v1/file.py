"""
File operation API interfaces
"""
import mimetypes
import os
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, UploadFile
from fastapi.params import File, Form, Query

from app.core.exceptions import ResourceNotFoundException
from app.schemas.file import (
    FileReadRequest, FileWriteRequest, FileReplaceRequest,
    FileSearchRequest, FileFindRequest, FileExistsRequest
)
from app.schemas.response import Response
from app.services.file import file_service
from starlette.responses import FileResponse

router = APIRouter()


@router.post("/read", response_model=Response)
async def read_file(request: FileReadRequest):
    """
    Read file content
    """
    result = await file_service.read_file(
        file=request.file,
        start_line=request.start_line,
        end_line=request.end_line,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message="File read successfully",
        data=result.model_dump()
    )


@router.post("/write", response_model=Response)
async def write_file(request: FileWriteRequest):
    """
    Write file content
    """
    result = await file_service.write_file(
        file=request.file,
        content=request.content,
        append=request.append,
        leading_newline=request.leading_newline,
        trailing_newline=request.trailing_newline,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message="File written successfully",
        data=result.model_dump()
    )


@router.post("/replace", response_model=Response)
async def replace_in_file(request: FileReplaceRequest):
    """
    Replace string in file
    """
    result = await file_service.str_replace(
        file=request.file,
        old_str=request.old_str,
        new_str=request.new_str,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message=f"Replacement completed, replaced {result.replaced_count} occurrences",
        data=result.model_dump()
    )


@router.post("/search", response_model=Response)
async def search_in_file(request: FileSearchRequest):
    """
    Search in file content
    """
    result = await file_service.find_in_content(
        file=request.file,
        regex=request.regex,
        sudo=request.sudo
    )

    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.matches)} matches",
        data=result.model_dump()
    )


@router.post("/find", response_model=Response)
async def find_files(request: FileFindRequest):
    """
    Find files by name pattern
    """
    result = await file_service.find_by_name(
        path=request.path,
        glob_pattern=request.glob
    )

    # Construct response
    return Response(
        success=True,
        message=f"Search completed, found {len(result.files)} files",
        data=result.model_dump()
    )


@router.post("/exists", response_model=Response)
async def check_file_exists(request: FileExistsRequest):
    """
    Check if file or directory exists
    """
    result = await file_service.check_exists(
        path=request.path
    )

    # Construct response
    return Response(
        success=True,
        message="File existence check completed",
        data=result.model_dump()
    )


@router.post("/upload", response_model=Response)
async def upload_file(
        file_data: UploadFile = File(..., description="待上传的文件"),
        target_path: str = Form(..., description="目标路径"),
        content_type: Optional[str] = Form(None, description="文件类型"),
):
    """
    上传文件到指定路径
    """
    result = await file_service.upload_file(
        file_data=file_data.file,
        filename=file_data.filename,
        target_path=target_path,
        content_type=content_type or file_data.content_type
    )
    return Response(
        success=True,
        message="文件上传成功",
        data=result.model_dump()
    )



@router.get("/download")
async def download_file(file_path: str = Query(...)):
    if not os.path.isfile(file_path):
        raise ResourceNotFoundException(f"File does not exist: {file_path}")

    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    safe_filename = quote(filename)
    content_disposition = (
        f"attachment; "
        f'filename="{safe_filename}"; '  
        f"filename*=UTF-8''{safe_filename}"
    )

    return FileResponse(
        file_path,
        media_type=mime_type,
        filename=filename,
        headers={
            "Content-Disposition": content_disposition
        }
    )
