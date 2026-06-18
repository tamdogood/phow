"""Action Inbox — the owner's running to-do, seeded from the Daily Brief + manual adds."""

import uuid
from typing import Any

from supabase import Client

from ..core.logging import get_logger
from ..repositories.action_item_repository import ActionItemRepository

logger = get_logger("action_inbox_service")

_STATUSES = {"open", "done", "dismissed"}


class ActionInboxService:
    def __init__(self, db: Client):
        self.db = db
        self.repo = ActionItemRepository(db)

    async def list_items(
        self, business_profile_id: str, status: str | None = "open", limit: int = 50
    ) -> list[dict[str, Any]]:
        return await self.repo.list_items(business_profile_id, status, limit)

    async def seed_from_brief(self, brief: dict) -> list[dict[str, Any]]:
        """Add the brief's top_actions as open items, skipping any already-open duplicate."""
        bp = brief.get("business_profile_id")
        actions = brief.get("top_actions") or []
        if not bp or not actions:
            return []
        existing = await self.repo.open_texts(bp)
        rows = [
            self._row(
                bp,
                text,
                source="daily_brief",
                source_id=brief.get("id"),
                session_id=brief.get("session_id"),
                user_id=brief.get("user_id"),
            )
            for text in self._new_actions(existing, actions)
        ]
        await self.repo.bulk_insert(rows)
        return rows

    async def create(
        self,
        business_profile_id: str,
        text: str,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        row = self._row(
            business_profile_id, text, source="manual", session_id=session_id, user_id=user_id
        )
        return await self.repo.insert(row)

    async def update_status(self, item_id: str, status: str) -> dict[str, Any] | None:
        if status not in _STATUSES:
            raise ValueError("Invalid status")
        return await self.repo.update_status(item_id, status)

    # ---- pure helpers (unit-tested) ---------------------------------------

    @staticmethod
    def _new_actions(existing_open_texts: list[str], actions: list[str]) -> list[str]:
        seen = {t.strip().lower() for t in existing_open_texts}
        out: list[str] = []
        for a in actions:
            key = (a or "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(a.strip())
        return out

    @staticmethod
    def _row(
        business_profile_id: str,
        text: str,
        *,
        source: str,
        source_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        row = {
            "id": str(uuid.uuid4()),
            "business_profile_id": business_profile_id,
            "text": (text or "").strip()[:500],
            "source": source,
            "status": "open",
        }
        for k, v in (
            ("source_id", source_id),
            ("session_id", session_id),
            ("user_id", user_id),
        ):
            if v:
                row[k] = v
        return row
