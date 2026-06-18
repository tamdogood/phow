"""Persistence for the Action Inbox."""

from typing import Any

from .base import BaseRepository


class ActionItemRepository(BaseRepository):
    async def list_items(
        self, business_profile_id: str, status: str | None = "open", limit: int = 50
    ) -> list[dict[str, Any]]:
        query = (
            self.db.table("action_items").select("*").eq("business_profile_id", business_profile_id)
        )
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data or []

    async def open_texts(self, business_profile_id: str) -> list[str]:
        result = (
            self.db.table("action_items")
            .select("text")
            .eq("business_profile_id", business_profile_id)
            .eq("status", "open")
            .execute()
        )
        return [r["text"] for r in (result.data or []) if r.get("text")]

    async def bulk_insert(self, rows: list[dict[str, Any]]) -> None:
        if rows:
            self.db.table("action_items").insert(rows).execute()

    async def insert(self, row: dict[str, Any]) -> dict[str, Any]:
        result = self.db.table("action_items").insert(row).execute()
        return result.data[0] if result.data else {}

    async def update_status(self, item_id: str, status: str) -> dict[str, Any] | None:
        result = (
            self.db.table("action_items").update({"status": status}).eq("id", item_id).execute()
        )
        return result.data[0] if result.data else None
