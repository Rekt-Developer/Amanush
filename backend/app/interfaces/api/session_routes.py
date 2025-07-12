from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator, List
from sse_starlette.event import ServerSentEvent
from datetime import datetime
import asyncio
import websockets
import logging

from app.application.services.agent_service import AgentService
from app.interfaces.schemas.request import ChatRequest, FileViewRequest, ShellViewRequest
from app.interfaces.schemas.response import (
    APIResponse, CreateSessionResponse, GetSessionResponse, 
    ListSessionItem, ListSessionResponse, ShellViewResponse, FileViewResponse
)
from app.interfaces.schemas.event import EventMapper
from app.domain.models.file import FileInfo

logger = logging.getLogger(__name__)
SESSION_POLL_INTERVAL = 5

def get_agent_service() -> AgentService:
    # Placeholder for dependency injection
    return None

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.put("", response_model=APIResponse[CreateSessionResponse])
async def create_session(
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[CreateSessionResponse]:
    session = await agent_service.create_session()
    return APIResponse.success(
        CreateSessionResponse(
            session_id=session.id,
        )
    )

@router.get("/{session_id}", response_model=APIResponse[GetSessionResponse])
async def get_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[GetSessionResponse]:
    session = await agent_service.get_session(session_id)
    return APIResponse.success(GetSessionResponse(
        session_id=session.id,
        title=session.title,
        events=EventMapper.events_to_sse_events(session.events)
    ))

@router.delete("/{session_id}", response_model=APIResponse[None])
async def delete_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.delete_session(session_id)
    return APIResponse.success()

@router.post("/{session_id}/stop", response_model=APIResponse[None])
async def stop_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[None]:
    await agent_service.stop_session(session_id)
    return APIResponse.success()

@router.get("", response_model=APIResponse[ListSessionResponse])
async def get_all_sessions(
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ListSessionResponse]:
    sessions = await agent_service.get_all_sessions()
    session_items = [
        ListSessionItem(
            session_id=session.id,
            title=session.title,
            status=session.status,
            unread_message_count=session.unread_message_count,
            latest_message=session.latest_message,
            latest_message_at=int(session.latest_message_at.timestamp()) if session.latest_message_at else None
        ) for session in sessions
    ]
    return APIResponse.success(ListSessionResponse(sessions=session_items))

@router.post("")
async def stream_sessions(
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        while True:
            sessions = await agent_service.get_all_sessions()
            session_items = [
                ListSessionItem(
                    session_id=session.id,
                    title=session.title,
                    status=session.status,
                    unread_message_count=session.unread_message_count,
                    latest_message=session.latest_message,
                    latest_message_at=int(session.latest_message_at.timestamp()) if session.latest_message_at else None
                ) for session in sessions
            ]
            yield ServerSentEvent(
                event="sessions",
                data=ListSessionResponse(sessions=session_items).model_dump_json()
            )
            await asyncio.sleep(SESSION_POLL_INTERVAL)
    return EventSourceResponse(event_generator())

@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[ServerSentEvent, None]:
        async for event in agent_service.chat(
            session_id=session_id,
            message=request.message,
            timestamp=datetime.fromtimestamp(request.timestamp) if request.timestamp else None,
            event_id=request.event_id,
            attachments=request.attachments
        ):
            logger.debug(f"Received event from chat: {event}")
            sse_event = EventMapper.event_to_sse_event(event)
            logger.debug(f"Received event: {sse_event}")
            if sse_event:
                yield ServerSentEvent(
                    event=sse_event.event,
                    data=sse_event.data.model_dump_json() if sse_event.data else None
                )

    return EventSourceResponse(event_generator())

@router.post("/{session_id}/shell")
async def view_shell(
    session_id: str,
    request: ShellViewRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[ShellViewResponse]:
    """View shell session output
    
    If the agent does not exist or fails to get shell output, an appropriate exception will be thrown and handled by the global exception handler
    
    Args:
        session_id: Session ID
        request: Shell view request containing session ID
        
    Returns:
        APIResponse with shell output
    """
    result = await agent_service.shell_view(session_id, request.session_id)
    return APIResponse.success(result)

@router.post("/{session_id}/file")
async def view_file(
    session_id: str,
    request: FileViewRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[FileViewResponse]:
    """View file content
    
    If the agent does not exist or fails to get file content, an appropriate exception will be thrown and handled by the global exception handler
    
    Args:
        session_id: Session ID
        request: File view request containing file path
        
    Returns:
        APIResponse with file content
    """
    result = await agent_service.file_view(session_id, request.file)
    return APIResponse.success(result)

@router.websocket("/{session_id}/vnc")
async def vnc_websocket(
    websocket: WebSocket,
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> None:
    """VNC WebSocket endpoint (binary mode)
    
    Establishes a connection with the VNC WebSocket service in the sandbox environment and forwards data bidirectionally
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID
    """
    
    await websocket.accept(subprotocol="binary")
    
    try:
    
        # Get sandbox environment address
        sandbox_ws_url = await agent_service.get_vnc_url(session_id)

        logger.info(f"Connecting to VNC WebSocket at {sandbox_ws_url}")
    
        # Connect to sandbox WebSocket
        async with websockets.connect(sandbox_ws_url) as sandbox_ws:
            logger.info(f"Connected to VNC WebSocket at {sandbox_ws_url}")
            # Create two tasks to forward data bidirectionally
            async def forward_to_sandbox():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await sandbox_ws.send(data)
                except WebSocketDisconnect:
                    logger.info("Web -> VNC connection closed")
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding data to sandbox: {e}")
            
            async def forward_from_sandbox():
                try:
                    while True:
                        data = await sandbox_ws.recv()
                        await websocket.send_bytes(data)
                except websockets.exceptions.ConnectionClosed:
                    logger.info("VNC -> Web connection closed")
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding data from sandbox: {e}")
            
            # Run two forwarding tasks concurrently
            forward_task1 = asyncio.create_task(forward_to_sandbox())
            forward_task2 = asyncio.create_task(forward_from_sandbox())
            
            # Wait for either task to complete (meaning connection has closed)
            done, pending = await asyncio.wait(
                [forward_task1, forward_task2],
                return_when=asyncio.FIRST_COMPLETED
            )

            logger.info("WebSocket connection closed")
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
    
    except ConnectionError as e:
        logger.error(f"Unable to connect to sandbox environment: {str(e)}")
        await websocket.close(code=1011, reason=f"Unable to connect to sandbox environment: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason=f"WebSocket error: {str(e)}")

@router.get("/{session_id}/files")
async def get_session_files(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> APIResponse[List[FileInfo]]:
    files = await agent_service.get_session_files(session_id)
    return APIResponse.success(files)