import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from .base import BaseRepository

_ALERT_COLS = (
    "id,subscription_id,business_profile_id,scan_id,title,url,source,source_domain,"
    "published_at,category,severity,relevance_score,summary,why_it_matters,"
    "suggested_action,status,created_at"
)


class RadarRepository(BaseRepository):
    """Persistence for Business Radar subscriptions, scans, and alerts."""

    # --- subscriptions ---

    async def get_subscription_by_profile(self, business_profile_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("radar_subscriptions")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("radar_subscriptions").select("*").eq("id", subscription_id).execute()
        )
        return result.data[0] if result.data else None

    async def create_subscription(self, data: dict[str, Any]) -> dict[str, Any]:
        data.setdefault("id", str(uuid.uuid4()))
        result = self.db.table("radar_subscriptions").insert(data).execute()
        return result.data[0] if result.data else {}

    async def update_subscription(
        self, subscription_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        result = (
            self.db.table("radar_subscriptions").update(data).eq("id", subscription_id).execute()
        )
        return result.data[0] if result.data else {}

    async def list_active_subscriptions(self) -> list[dict[str, Any]]:
        result = self.db.table("radar_subscriptions").select("*").eq("status", "active").execute()
        return result.data or []

    # --- scans ---

    async def create_scan(self, subscription_id: str) -> dict[str, Any]:
        data = {"id": str(uuid.uuid4()), "subscription_id": subscription_id, "status": "running"}
        result = self.db.table("radar_scans").insert(data).execute()
        return result.data[0] if result.data else {}

    async def update_scan(self, scan_id: str, data: dict[str, Any]) -> dict[str, Any]:
        result = self.db.table("radar_scans").update(data).eq("id", scan_id).execute()
        return result.data[0] if result.data else {}

    async def latest_scan(self, subscription_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("radar_scans")
            .select("*")
            .eq("subscription_id", subscription_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    # --- alerts ---

    async def save_alerts(self, alerts: list[dict[str, Any]]) -> None:
        if alerts:
            self.db.table("radar_alerts").insert(alerts).execute()

    async def list_alerts(
        self, business_profile_id: str, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        query = (
            self.db.table("radar_alerts")
            .select(_ALERT_COLS)
            .eq("business_profile_id", business_profile_id)
        )
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return result.data or []

    async def recent_alerts(
        self, business_profile_id: str, since: str, limit: int = 60
    ) -> list[dict[str, Any]]:
        """Non-dismissed alerts created since ``since`` (ISO ts), newest first."""
        result = (
            self.db.table("radar_alerts")
            .select(_ALERT_COLS)
            .eq("business_profile_id", business_profile_id)
            .neq("status", "dismissed")
            .gte("created_at", since)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def last_alert_by_category(
        self, subscription_id: str, category: str
    ) -> dict[str, Any] | None:
        """Most recent alert in a category (used as a rolling baseline for signal diffs)."""
        result = (
            self.db.table("radar_alerts")
            .select("*")
            .eq("subscription_id", subscription_id)
            .eq("category", category)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def recent_alert_urls(self, subscription_id: str, days: int = 30) -> set[str]:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self.db.table("radar_alerts")
            .select("url")
            .eq("subscription_id", subscription_id)
            .gte("created_at", since)
            .execute()
        )
        return {r["url"] for r in (result.data or []) if r.get("url")}

    async def count_unread(self, business_profile_id: str) -> int:
        result = (
            self.db.table("radar_alerts")
            .select("id", count="exact")
            .eq("business_profile_id", business_profile_id)
            .eq("status", "new")
            .execute()
        )
        return result.count or 0

    async def mark_alert(self, alert_id: str, status: str) -> dict[str, Any] | None:
        result = (
            self.db.table("radar_alerts").update({"status": status}).eq("id", alert_id).execute()
        )
        return result.data[0] if result.data else None
