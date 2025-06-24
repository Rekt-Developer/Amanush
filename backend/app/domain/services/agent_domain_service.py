import json
from typing import Optional, AsyncGenerator, List, Dict, Any
import logging
from datetime import datetime
import httpx
from app.domain.models.session import Session, SessionStatus
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.search import SearchEngine
from app.domain.events.agent_events import BaseEvent, ErrorEvent, DoneEvent, PlanEvent, StepEvent, ToolEvent, \
    MessageEvent, WaitEvent, AgentEventFactory
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.agent_task_runner import AgentTaskRunner
from app.domain.external.task import Task
from app.domain.utils.json_parser import JsonParser
from typing import Type

from app.infrastructure.external.file.file_operate import FileOperationFactory
from app.interfaces.schemas.request import AttachmentBindRequest

# Setup logging
logger = logging.getLogger(__name__)


def _generate_attachment_analysis_message(attachments: List[AttachmentBindRequest],
                                          attachment_dir: str) -> str:
    attachment_info = []
    for attachment in attachments:
        attachment_info.append({
            "filename": attachment.filename,
            "content_type": attachment.content_type,
            "file_size": attachment.file_size,
            "path": f"/app/{attachment_dir}/{attachment.filename}",
            "storage_url": attachment.storage_url,
            "storage_type": attachment.storage_type
        })

    return f"""
ATTACHMENT ANALYSIS REQUEST

User has uploaded the following attachments. Please analyze the content and generate an appropriate execution plan.

ATTACHMENT INFORMATION:
{json.dumps(attachment_info, indent=2, ensure_ascii=False)}

FILE LOCATION AND USAGE:
- All uploaded files are located in: /app/{attachment_dir}/
- To read these files, use the exact paths shown above
- Example: file_read(file="/app/{attachment_dir}/filename.ext")
- Do not use /home/ubuntu/ paths for these uploaded files

ANALYSIS REQUIREMENTS:
1. Analyze the type and content of each attachment
2. Identify the purpose and functionality of the files
3. Consider the user's chat message context
4. Generate a detailed execution plan
5. Ensure the plan can properly handle these attachment files

EXECUTION GUIDELINES:
- Use appropriate tools to examine file contents
- Provide detailed analysis of each file
- Create actionable steps for file processing
- Consider file compatibility and system requirements
- Document any limitations or special considerations
- Use the exact file paths provided above when reading files

Please proceed with the analysis and provide a comprehensive execution plan.
"""


class AgentDomainService:
    """
    Agent domain service, responsible for coordinating the work of planning agent and execution agent
    """

    def __init__(
            self,
            agent_repository: AgentRepository,
            session_repository: SessionRepository,
            llm: LLM,
            sandbox_cls: Type[Sandbox],
            task_cls: Type[Task],
            json_parser: JsonParser,
            search_engine: Optional[SearchEngine] = None
    ):
        self._repository = agent_repository
        self._session_repository = session_repository
        self._llm = llm
        self._sandbox_cls = sandbox_cls
        self._search_engine = search_engine
        self._task_cls = task_cls
        self._json_parser = json_parser
        self._storage_factory = FileOperationFactory()
        logger.info("AgentDomainService initialization completed")

    async def shutdown(self) -> None:
        """Clean up all Agent's resources"""
        logger.info(f"Starting to close all Agents")
        await self._task_cls.destroy()
        logger.info("All agents closed successfully")

    async def _create_task(self, session: Session) -> Task:
        """Create a new agent task"""
        sandbox = None
        sandbox_id = session.sandbox_id
        if sandbox_id:
            sandbox = await self._sandbox_cls.get(sandbox_id)
        if not sandbox:
            sandbox = await self._sandbox_cls.create()
            session.sandbox_id = sandbox.id
            await self._session_repository.save(session)
        browser = await sandbox.get_browser()
        if not browser:
            logger.error(f"Failed to get browser for Sandbox {sandbox_id}")
            raise RuntimeError(f"Failed to get browser for Sandbox {sandbox_id}")

        await self._session_repository.save(session)

        task_runner = AgentTaskRunner(
            session_id=session.id,
            agent_id=session.agent_id,
            llm=self._llm,
            sandbox=sandbox,
            browser=browser,
            search_engine=self._search_engine,
            session_repository=self._session_repository,
            json_parser=self._json_parser,
            agent_repository=self._repository,
        )

        task = self._task_cls.create(task_runner)
        session.task_id = task.id
        await self._session_repository.save(session)

        return task

    async def _get_task(self, session: Session) -> Optional[Task]:
        """Get a task for the given session"""

        task_id = session.task_id
        if not task_id:
            return None

        return self._task_cls.get(task_id)

    async def stop_session(self, session_id: str) -> None:
        """Stop a session"""
        session = await self._session_repository.find_by_id(session_id)
        if not session:
            logger.error(f"Attempted to stop non-existent Session {session_id}")
            raise RuntimeError("Session not found")
        task = await self._get_task(session)
        if task:
            task.cancel()
        await self._session_repository.update_status(session_id, SessionStatus.COMPLETED)

    async def chat(
            self,
            session_id: str,
            message: Optional[str] = None,
            timestamp: Optional[datetime] = None,
            latest_event_id: Optional[str] = None,
            attachments: Optional[List[AttachmentBindRequest]] = None
    ) -> AsyncGenerator[BaseEvent, None]:
        """
        Chat with an agent
        """

        try:
            session = await self._session_repository.find_by_id(session_id)
            if not session:
                logger.error(f"Attempted to chat with non-existent Session {session_id}")
                raise RuntimeError("Session not found")

            task = await self._get_task(session)

            if message:
                if session.status != SessionStatus.RUNNING:
                    task = await self._create_task(session)
                    if not task:
                        raise RuntimeError("Failed to create task")

                await self._session_repository.update_latest_message(session_id, message, timestamp or datetime.now())

                # 处理附件并生成附件信息
                attachments_info = None
                if attachments:
                    await self._process_attachments(session_id, attachments, task)
                    # 生成附件信息字符串，用于传递给大模型
                    attachment_dir = f"upload/{session_id}"
                    attachments_info = _generate_attachment_analysis_message(attachments, attachment_dir)

                if attachments_info:
                    message_data = json.dumps({"message": message, "attachments_info": attachments_info})
                else:
                    message_data = message

                message_id = await task.input_stream.put(message_data)
                message_event = MessageEvent(message=message, role="user", id=message_id)
                await self._session_repository.add_event(session_id, message_event)
                await task.run()
                logger.debug(f"Put message into Session {session_id}'s event queue: {message[:50]}...")

            logger.info(f"Session {session_id} started")
            logger.debug(f"Session {session_id} task: {task}")

            while task and not task.done:
                event_id, event_str = await task.output_stream.get(start_id=latest_event_id, block_ms=0)
                latest_event_id = event_id
                if event_str is None:
                    logger.debug(f"No event found in Session {session_id}'s event queue")
                    continue
                event = AgentEventFactory.from_json(event_str)
                event.id = event_id
                logger.debug(f"Got event from Session {session_id}'s event queue: {type(event).__name__}")
                await self._session_repository.update_unread_message_count(session_id, 0)
                yield event
                if isinstance(event, (DoneEvent, ErrorEvent, WaitEvent)):
                    break

            logger.info(f"Session {session_id} completed")

        except Exception as e:
            logger.exception(f"Error in Session {session_id}")
            event = ErrorEvent(error=str(e))
            await self._session_repository.add_event(session_id, event)
            yield event  # TODO: raise api exception
        finally:
            await self._session_repository.update_unread_message_count(session_id, 0)

    async def _process_attachments(self, session_id: str, attachments: List[AttachmentBindRequest], task: Task) -> None:
        """
        Process attachments: upload to sandbox
        """
        session = await self._session_repository.find_by_id(session_id)
        if not session.sandbox_id:
            logger.warning(f"No sandbox found for session {session_id}")
            return

        sandbox = await self._sandbox_cls.get(session.sandbox_id)
        if not sandbox:
            logger.warning(f"Sandbox not found for session {session_id}")
            return

        attachment_dir = f"upload/{session_id}"
        storage = await self._storage_factory.create_storage()
        sandbox_ip = sandbox.ip if hasattr(sandbox, 'ip') else None
        upload_url = f"http://{sandbox_ip}:8080/api/v1/file/upload"

        for attachment in attachments:
            file_content = await storage.download_file(attachment.storage_url)
            file_data = file_content['content']

            if isinstance(file_data, str):
                file_data = file_data.encode('utf-8')

            files = {
                "file_data": (attachment.filename, file_data, attachment.content_type)
            }
            data = {"target_path": attachment_dir}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(upload_url, files=files, data=data)
                result = response.json()

                if not result.get("success"):
                    raise RuntimeError(
                        f"Upload failed for {attachment.filename}: {result.get('message', 'Unknown error')}")

                logger.info(f"Successfully uploaded {attachment.filename} to {attachment_dir}")

        logger.info(f"Processed {len(attachments)} attachments for session {session_id}")
