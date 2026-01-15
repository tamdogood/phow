import uuid
from typing import Any
from .base import BaseRepository


class MessageRepository(BaseRepository):
    """Repository for message database operations."""

    async def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new message."""
        message_id = str(uuid.uuid4())
        result = (
            self.db.table("messages")
            .insert(
                {
                    "id": message_id,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_conversation(
        self, conversation_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all messages in a conversation."""
        result = (
            self.db.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_latest(self, conversation_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get latest N messages in a conversation."""
        result = (
            self.db.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        # Reverse to get chronological order
        return list(reversed(result.data or []))

    async def delete_by_conversation(self, conversation_id: str) -> bool:
        """Delete all messages in a conversation."""
        result = self.db.table("messages").delete().eq("conversation_id", conversation_id).execute()
        return True  # Cascade delete handles this
