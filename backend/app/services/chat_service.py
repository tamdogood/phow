from typing import AsyncIterator, Any
from supabase import Client
from ..repositories import ConversationRepository, MessageRepository
from ..core.tool_registry import ToolRegistry
from ..tools.base import ToolContext


class ChatService:
    """Service for handling chat operations."""

    def __init__(self, db: Client):
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    async def get_or_create_conversation(
        self,
        session_id: str,
        conversation_id: str | None,
        tool_id: str,
    ) -> str:
        """Get existing conversation or create a new one."""
        if conversation_id:
            # Verify conversation exists and belongs to session
            if await self.conversation_repo.verify_ownership(conversation_id, session_id):
                return conversation_id

        # Create new conversation
        conversation = await self.conversation_repo.create(
            session_id=session_id,
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
        return await self.message_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )

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
        """
        Process a user message and stream the response.

        Yields tuples of (chunk_content, event_type)
        Event types: 'chunk', 'done', 'error'
        """
        # Get or create conversation
        conv_id = await self.get_or_create_conversation(session_id, conversation_id, tool_id)

        # Save user message
        await self.save_message(conv_id, "user", message)

        # Get the tool
        tool = ToolRegistry.get(tool_id)
        if not tool:
            yield ("Tool not found", "error")
            return

        # Create tool context
        context = ToolContext(
            session_id=session_id,
            conversation_id=conv_id,
        )

        # Stream the tool response
        full_response = []
        try:
            async for chunk in tool.process_stream(message, context):
                full_response.append(chunk)
                yield (chunk, "chunk")

            # Save assistant response
            response_text = "".join(full_response)
            await self.save_message(conv_id, "assistant", response_text)

            # Send done event with conversation ID
            yield (conv_id, "done")

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            yield (error_msg, "error")

    async def list_conversations(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """List all conversations for a session."""
        return await self.conversation_repo.get_by_session(session_id, limit)

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get all messages in a conversation."""
        return await self.message_repo.get_by_conversation(conversation_id)
