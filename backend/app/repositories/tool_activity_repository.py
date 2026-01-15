"""Repository for tool activity tracking."""

from typing import Any
from .base import BaseRepository


class ToolActivityRepository(BaseRepository):
    """Repository for storing and retrieving tool activities."""

    table = "tool_activities"

    async def start_activity(
        self,
        session_id: str,
        tool_id: str,
        tool_name: str,
        input_args: dict | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Record the start of a tool activity."""
        data = {
            "session_id": session_id,
            "tool_id": tool_id,
            "tool_name": tool_name,
            "status": "started",
            "input_args": input_args,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id

        result = self.db.table(self.table).insert(data).execute()
        return result.data[0]

    async def complete_activity(
        self,
        activity_id: str,
        output_data: dict | None = None,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        """Mark a tool activity as completed."""
        data = {"status": "completed", "completed_at": "now()"}
        if output_data is not None:
            data["output_data"] = output_data
        if latency_ms is not None:
            data["latency_ms"] = latency_ms

        result = self.db.table(self.table).update(data).eq("id", activity_id).execute()
        return result.data[0] if result.data else {}

    async def fail_activity(
        self,
        activity_id: str,
        error_message: str,
        latency_ms: int | None = None,
    ) -> dict[str, Any]:
        """Mark a tool activity as failed."""
        data = {
            "status": "failed",
            "error_message": error_message,
            "completed_at": "now()",
        }
        if latency_ms is not None:
            data["latency_ms"] = latency_ms

        result = self.db.table(self.table).update(data).eq("id", activity_id).execute()
        return result.data[0] if result.data else {}

    async def get_by_conversation(
        self, conversation_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get all tool activities for a conversation."""
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    async def get_by_session(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get all tool activities for a session."""
        result = (
            self.db.table(self.table)
            .select("*")
            .eq("session_id", session_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    async def get_stats(self, tool_id: str | None = None) -> dict[str, Any]:
        """Get tool activity statistics."""
        query = self.db.table(self.table).select("tool_id, tool_name, status, latency_ms")
        if tool_id:
            query = query.eq("tool_id", tool_id)
        result = query.execute()

        stats = {
            "total_calls": 0,
            "completed": 0,
            "failed": 0,
            "avg_latency_ms": 0,
            "by_tool": {},
        }
        latencies = []

        for row in result.data:
            stats["total_calls"] += 1
            if row["status"] == "completed":
                stats["completed"] += 1
            elif row["status"] == "failed":
                stats["failed"] += 1

            if row.get("latency_ms"):
                latencies.append(row["latency_ms"])

            tool_name = row["tool_name"]
            if tool_name not in stats["by_tool"]:
                stats["by_tool"][tool_name] = {"calls": 0, "completed": 0, "failed": 0}
            stats["by_tool"][tool_name]["calls"] += 1
            if row["status"] == "completed":
                stats["by_tool"][tool_name]["completed"] += 1
            elif row["status"] == "failed":
                stats["by_tool"][tool_name]["failed"] += 1

        if latencies:
            stats["avg_latency_ms"] = sum(latencies) // len(latencies)

        return stats
