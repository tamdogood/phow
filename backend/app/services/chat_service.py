import time
from typing import AsyncIterator, Any
from supabase import Client
from ..repositories import ConversationRepository, MessageRepository
from ..core.tool_registry import ToolRegistry
from ..core.logging import get_logger
from ..tools.base import ToolContext
from .tracking_service import TrackingService

logger = get_logger("chat_service")


class ChatService:
    """Service for handling chat operations."""

    def __init__(self, db: Client):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
        self.tracking_service = TrackingService(db)

    async def get_or_create_conversation(
        self,
        session_id: str,
        conversation_id: str | None,
        tool_id: str,
    ) -> str:
        """Get existing conversation or create a new one."""
        if conversation_id:
            if await self.conversation_repo.verify_ownership(
                conversation_id, session_id
            ):
                logger.debug(
                    "Using existing conversation", conversation_id=conversation_id
                )
                return conversation_id

        conversation = await self.conversation_repo.create(
            session_id=session_id, tool_id=tool_id
        )
        logger.info(
            "Created new conversation",
            conversation_id=conversation["id"],
            tool_id=tool_id,
        )
        return conversation["id"]

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save a message to the database."""
        result = await self.message_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        logger.debug("Saved message", role=role, content_length=len(content))
        return result

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get conversation message history."""
        return await self.message_repo.get_latest(conversation_id, limit)

    async def process_message(
        self,
        session_id: str,
        tool_id: str,
        message: str,
        conversation_id: str | None = None,
    ) -> AsyncIterator[tuple[str, str | None]]:
        """Process a user message and stream the response."""
        logger.info(
            "Processing message",
            session_id=session_id[:8],
            tool_id=tool_id,
            message_length=len(message),
        )

        conv_id = await self.get_or_create_conversation(
            session_id, conversation_id, tool_id
        )
        await self.save_message(conv_id, "user", message)

        tool = ToolRegistry.get(tool_id)
        if not tool:
            logger.error("Tool not found", tool_id=tool_id)
            yield ("Tool not found", "error")
            return

        logger.info("Invoking tool", tool_id=tool_id, tool_name=tool.name)
        context = ToolContext(
            session_id=session_id,
            conversation_id=conv_id,
            tracking_service=self.tracking_service,
        )

        start_time = time.time()
        activity_id = await self.tracking_service.start_tool_activity(
            session_id=session_id,
            tool_id=tool_id,
            tool_name=tool.name,
            input_args={"message": message[:500]},
            conversation_id=conv_id,
        )

        full_response = []
        try:
            async for chunk in tool.process_stream(message, context):
                full_response.append(chunk)
                yield (chunk, "chunk")

            response_text = "".join(full_response)
            await self.save_message(conv_id, "assistant", response_text)

            latency_ms = int((time.time() - start_time) * 1000)
            await self.tracking_service.complete_tool_activity(
                activity_id=activity_id,
                output_data={"response_length": len(response_text)},
                latency_ms=latency_ms,
            )
            logger.info(
                "Message processed successfully",
                response_length=len(response_text),
                latency_ms=latency_ms,
            )

            yield (conv_id, "done")

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            await self.tracking_service.fail_tool_activity(
                activity_id=activity_id,
                error_message=str(e),
                latency_ms=latency_ms,
            )
            logger.error(
                "Error processing message", error=str(e), error_type=type(e).__name__
            )
            yield (f"Error processing message: {str(e)}", "error")

    async def list_conversations(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List all conversations for a session."""
        return await self.conversation_repo.get_by_session(session_id, limit)

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get all messages in a conversation."""
        return await self.message_repo.get_by_conversation(conversation_id)
