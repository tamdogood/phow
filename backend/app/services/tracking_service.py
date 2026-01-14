"""Service for tracking LLM responses and tool activities."""

from typing import Any
from supabase import Client
from ..repositories import LLMResponseRepository, ToolActivityRepository
from ..core.logging import get_logger

logger = get_logger("tracking")


class TrackingService:
    """Service for tracking LLM and tool activities."""

    def __init__(self, db: Client):
        self.llm_repo = LLMResponseRepository(db)
        self.tool_repo = ToolActivityRepository(db)

    async def log_llm_response(
        self,
        conversation_id: str,
        provider: str,
        model: str,
        input_messages: list[dict],
        output_content: str,
        message_id: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        metadata: dict | None = None,
    ) -> dict[str, Any]:
        """Log an LLM response to the database."""
        try:
            result = await self.llm_repo.create(
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                input_messages=input_messages,
                output_content=output_content,
                message_id=message_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                metadata=metadata,
            )
            logger.info(
                "Logged LLM response",
                provider=provider,
                model=model,
                tokens=total_tokens,
                latency_ms=latency_ms,
            )
            return result
        except Exception as e:
            logger.error("Failed to log LLM response", error=str(e))
            return {}

    async def start_tool_activity(
        self,
        session_id: str,
        tool_id: str,
        tool_name: str,
        input_args: dict | None = None,
        conversation_id: str | None = None,
    ) -> str | None:
        """Start tracking a tool activity. Returns the activity ID."""
        try:
            result = await self.tool_repo.start_activity(
                session_id=session_id,
                tool_id=tool_id,
                tool_name=tool_name,
                input_args=input_args,
                conversation_id=conversation_id,
            )
            logger.info("Tool activity started", tool_id=tool_id, tool_name=tool_name)
            return result.get("id")
        except Exception as e:
            logger.error("Failed to start tool activity", error=str(e))
            return None

    async def complete_tool_activity(
        self,
        activity_id: str,
        output_data: dict | None = None,
        latency_ms: int | None = None,
    ) -> None:
        """Mark a tool activity as completed."""
        if not activity_id:
            return
        try:
            await self.tool_repo.complete_activity(
                activity_id=activity_id,
                output_data=output_data,
                latency_ms=latency_ms,
            )
            logger.info(
                "Tool activity completed",
                activity_id=activity_id,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.error("Failed to complete tool activity", error=str(e))

    async def fail_tool_activity(
        self,
        activity_id: str,
        error_message: str,
        latency_ms: int | None = None,
    ) -> None:
        """Mark a tool activity as failed."""
        if not activity_id:
            return
        try:
            await self.tool_repo.fail_activity(
                activity_id=activity_id,
                error_message=error_message,
                latency_ms=latency_ms,
            )
            logger.warning(
                "Tool activity failed", activity_id=activity_id, error=error_message
            )
        except Exception as e:
            logger.error("Failed to log tool failure", error=str(e))

    async def get_conversation_llm_history(self, conversation_id: str) -> list[dict]:
        """Get LLM response history for a conversation."""
        return await self.llm_repo.get_by_conversation(conversation_id)

    async def get_conversation_tool_history(self, conversation_id: str) -> list[dict]:
        """Get tool activity history for a conversation."""
        return await self.tool_repo.get_by_conversation(conversation_id)

    async def get_usage_stats(self, conversation_id: str | None = None) -> dict:
        """Get combined usage statistics."""
        llm_stats = await self.llm_repo.get_usage_stats(conversation_id)
        tool_stats = await self.tool_repo.get_stats()
        return {"llm": llm_stats, "tools": tool_stats}
