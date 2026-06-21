"""Repositories for the Reputation Hub: platform connections and reviews."""

from typing import Any
from .base import BaseRepository


class ReviewConnectionRepository(BaseRepository):
    """OAuth connections to review platforms (Google Business Profile, etc.)."""

    async def upsert(
        self, business_profile_id: str, platform: str = "google", **fields
    ) -> dict[str, Any]:
        data = {"business_profile_id": business_profile_id, "platform": platform, **fields}
        data = {k: v for k, v in data.items() if v is not None}
        result = (
            self.db.table("review_connections")
            .upsert(data, on_conflict="business_profile_id,platform")
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_id(self, connection_id: str) -> dict[str, Any] | None:
        result = self.db.table("review_connections").select("*").eq("id", connection_id).execute()
        return result.data[0] if result.data else None

    async def get_for_profile(self, business_profile_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("review_connections")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def get_connected(
        self, business_profile_id: str, platform: str = "google"
    ) -> dict[str, Any] | None:
        result = (
            self.db.table("review_connections")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .eq("platform", platform)
            .eq("status", "connected")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_all_connected(self) -> list[dict[str, Any]]:
        result = self.db.table("review_connections").select("*").eq("status", "connected").execute()
        return result.data or []

    async def update(self, connection_id: str, **fields) -> dict[str, Any] | None:
        updates = {k: v for k, v in fields.items() if v is not None}
        if not updates:
            return await self.get_by_id(connection_id)
        result = (
            self.db.table("review_connections").update(updates).eq("id", connection_id).execute()
        )
        return result.data[0] if result.data else None

    async def delete(self, connection_id: str) -> bool:
        result = self.db.table("review_connections").delete().eq("id", connection_id).execute()
        return bool(result.data)


class ReviewRepository(BaseRepository):
    """Normalized reviews with inline sentiment and owner response."""

    async def upsert(self, **fields) -> dict[str, Any]:
        # Omit None so re-syncs never clobber existing response columns.
        data = {k: v for k, v in fields.items() if v is not None}
        result = (
            self.db.table("reviews").upsert(data, on_conflict="source,external_review_id").execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_id(self, review_id: str) -> dict[str, Any] | None:
        result = self.db.table("reviews").select("*").eq("id", review_id).execute()
        return result.data[0] if result.data else None

    async def get_inbox(
        self,
        business_profile_id: str,
        review_filter: str = "all",
        source: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = self.db.table("reviews").select("*").eq("business_profile_id", business_profile_id)
        if source:
            query = query.eq("source", source)
        if review_filter == "unreplied":
            query = query.neq("response_status", "responded")
        elif review_filter == "negative":
            query = query.or_("rating.lte.3,sentiment.eq.negative")
        result = query.order("review_created_at", desc=True).limit(limit).execute()
        return result.data or []

    async def get_all_for_profile(self, business_profile_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("reviews")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("review_created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def update(self, review_id: str, **fields) -> dict[str, Any] | None:
        updates = {k: v for k, v in fields.items() if v is not None}
        if not updates:
            return await self.get_by_id(review_id)
        result = self.db.table("reviews").update(updates).eq("id", review_id).execute()
        return result.data[0] if result.data else None
