import uuid
from typing import Any
from .base import BaseRepository


class ConversationRepository(BaseRepository):
    """Repository for conversation database operations."""

    async def create(
        self,
        session_id: str,
        tool_id: str,
        title: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        result = (
            self.db.table("conversations")
            .insert(
                {
                    "id": conversation_id,
                    "session_id": session_id,
                    "tool_id": tool_id,
                    "title": title,
                    "user_id": user_id,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation by ID."""
        result = self.db.table("conversations").select("*").eq("id", conversation_id).execute()
        return result.data[0] if result.data else None

    async def get_by_session(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get all conversations for a session."""
        result = (
            self.db.table("conversations")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def update_title(self, conversation_id: str, title: str) -> dict[str, Any] | None:
        """Update conversation title."""
        result = (
            self.db.table("conversations")
            .update({"title": title})
            .eq("id", conversation_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        result = self.db.table("conversations").delete().eq("id", conversation_id).execute()
        return bool(result.data)

    async def verify_ownership(self, conversation_id: str, session_id: str) -> bool:
        """Verify conversation belongs to session."""
        result = (
            self.db.table("conversations")
            .select("id")
            .eq("id", conversation_id)
            .eq("session_id", session_id)
            .execute()
        )
        return bool(result.data)
