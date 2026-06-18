"""Persistence for the Daily Brief (one row per business per day)."""

from datetime import date
from typing import Any

from .base import BaseRepository


class DailyBriefRepository(BaseRepository):
    async def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert or replace the brief for a (business_profile_id, brief_date)."""
        result = (
            self.db.table("daily_briefs")
            .upsert(data, on_conflict="business_profile_id,brief_date")
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_latest(self, business_profile_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("daily_briefs")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("brief_date", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_by_date(self, business_profile_id: str, brief_date: str) -> dict[str, Any] | None:
        result = (
            self.db.table("daily_briefs")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .eq("brief_date", brief_date)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def exists_for_date(self, business_profile_id: str, brief_date: str) -> bool:
        return await self.get_by_date(business_profile_id, brief_date) is not None

    @staticmethod
    def today() -> str:
        return date.today().isoformat()
