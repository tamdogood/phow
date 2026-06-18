import uuid
from typing import Any
from .base import BaseRepository

_SUMMARY_COLS = (
    "id,concept,location_address,status,verdict,viability_score,title,created_at,completed_at"
)


class FeasibilityRepository(BaseRepository):
    """Persistence for feasibility study reports."""

    TABLE = "feasibility_reports"

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        data.setdefault("id", str(uuid.uuid4()))
        result = self.db.table(self.TABLE).insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_by_id(self, report_id: str) -> dict[str, Any] | None:
        result = self.db.table(self.TABLE).select("*").eq("id", report_id).execute()
        return result.data[0] if result.data else None

    async def update(self, report_id: str, data: dict[str, Any]) -> dict[str, Any]:
        result = self.db.table(self.TABLE).update(data).eq("id", report_id).execute()
        return result.data[0] if result.data else {}

    async def list_by_session(self, session_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table(self.TABLE)
            .select(_SUMMARY_COLS)
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def list_by_user(self, user_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table(self.TABLE)
            .select(_SUMMARY_COLS)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def delete(self, report_id: str) -> bool:
        result = self.db.table(self.TABLE).delete().eq("id", report_id).execute()
        return bool(result.data)
