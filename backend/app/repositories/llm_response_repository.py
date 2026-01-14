"""Repository for LLM response tracking."""

from typing import Any
from .base import BaseRepository


class LLMResponseRepository(BaseRepository):
    """Repository for storing and retrieving LLM responses."""

    table = "llm_responses"

    async def create(
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
        """Record an LLM response."""
        data = {
            "conversation_id": conversation_id,
            "provider": provider,
            "model": model,
            "input_messages": input_messages,
            "output_content": output_content,
        }
        if message_id:
            data["message_id"] = message_id
        if prompt_tokens is not None:
            data["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            data["completion_tokens"] = completion_tokens
        if total_tokens is not None:
            data["total_tokens"] = total_tokens
        if latency_ms is not None:
            data["latency_ms"] = latency_ms
        if metadata:
            data["metadata"] = metadata

        result = self.db.table(self.table).insert(data).execute()
        return result.data[0]

    async def get_by_conversation(
        self, conversation_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get all LLM responses for a conversation."""
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    async def get_usage_stats(
        self, conversation_id: str | None = None
    ) -> dict[str, Any]:
        """Get token usage statistics."""
        query = self.db.table(self.table).select(
            "provider, model, prompt_tokens, completion_tokens, total_tokens"
        )
        if conversation_id:
            query = query.eq("conversation_id", conversation_id)
        result = query.execute()

        stats = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "by_provider": {},
        }
        for row in result.data:
            stats["total_prompt_tokens"] += row.get("prompt_tokens") or 0
            stats["total_completion_tokens"] += row.get("completion_tokens") or 0
            stats["total_tokens"] += row.get("total_tokens") or 0

            provider = row["provider"]
            if provider not in stats["by_provider"]:
                stats["by_provider"][provider] = {"calls": 0, "tokens": 0}
            stats["by_provider"][provider]["calls"] += 1
            stats["by_provider"][provider]["tokens"] += row.get("total_tokens") or 0

        return stats
