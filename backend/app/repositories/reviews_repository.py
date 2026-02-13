"""Repositories for Reputation Hub persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .base import BaseRepository


class ReviewSourceRepository(BaseRepository):
    """Repository for review source connection state."""

    async def list_by_profile(self, business_profile_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("review_sources")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []

    async def get_by_profile_source(
        self,
        business_profile_id: str,
        source: str,
    ) -> dict[str, Any] | None:
        result = (
            self.db.table("review_sources")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .eq("source", source)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def upsert(
        self,
        business_profile_id: str,
        source: str,
        **fields,
    ) -> dict[str, Any]:
        payload = {
            "business_profile_id": business_profile_id,
            "source": source,
            **{k: v for k, v in fields.items() if v is not None},
        }
        result = (
            self.db.table("review_sources")
            .upsert(payload, on_conflict="business_profile_id,source")
            .execute()
        )
        return result.data[0] if result.data else {}

    async def disconnect(self, business_profile_id: str, source: str) -> dict[str, Any] | None:
        result = (
            self.db.table("review_sources")
            .update(
                {
                    "status": "disconnected",
                    "access_token_encrypted": None,
                    "refresh_token_encrypted": None,
                    "token_expires_at": None,
                    "last_error": None,
                }
            )
            .eq("business_profile_id", business_profile_id)
            .eq("source", source)
            .execute()
        )
        return result.data[0] if result.data else None

    async def mark_synced(self, business_profile_id: str, source: str):
        now = datetime.now(timezone.utc).isoformat()
        (
            self.db.table("review_sources")
            .update({"last_synced_at": now, "last_error": None})
            .eq("business_profile_id", business_profile_id)
            .eq("source", source)
            .execute()
        )


class ReviewRepository(BaseRepository):
    """Repository for reviews inbox data."""

    async def upsert_many(
        self,
        business_profile_id: str,
        source_connection_id: str | None,
        reviews: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not reviews:
            return []

        rows = []
        for item in reviews:
            external_review_id = item.get("external_review_id")
            source = item.get("source")
            if not external_review_id or not source:
                continue

            row = {
                "business_profile_id": business_profile_id,
                "source_connection_id": source_connection_id,
                "source": source,
                "external_review_id": external_review_id,
                "external_url": item.get("external_url"),
                "reviewer_name": item.get("reviewer_name"),
                "rating": item.get("rating") or 0,
                "title": item.get("title"),
                "content": item.get("content"),
                "review_created_at": item.get("review_created_at"),
                "raw_payload": item.get("raw_payload") or {},
            }
            rows.append(row)

        if not rows:
            return []

        result = self.db.table("reviews").upsert(rows, on_conflict="source,external_review_id").execute()
        return result.data or []

    async def get_by_id_and_profile(
        self,
        review_id: str,
        business_profile_id: str,
    ) -> dict[str, Any] | None:
        result = (
            self.db.table("reviews")
            .select("*")
            .eq("id", review_id)
            .eq("business_profile_id", business_profile_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_inbox(
        self,
        business_profile_id: str,
        *,
        source: str | None = None,
        unreplied_only: bool = False,
        min_rating: int | None = None,
        max_rating: int | None = None,
        search: str | None = None,
        cursor: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        query = (
            self.db.table("reviews")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("review_created_at", desc=True)
            .limit(limit)
        )

        if source:
            query = query.eq("source", source)
        if unreplied_only:
            query = query.eq("reply_status", "unreplied")
        if min_rating is not None:
            query = query.gte("rating", min_rating)
        if max_rating is not None:
            query = query.lte("rating", max_rating)
        if search:
            query = query.ilike("content", f"%{search}%")
        if cursor:
            query = query.lt("review_created_at", cursor)

        result = query.execute()
        return result.data or []

    async def list_by_profile(
        self,
        business_profile_id: str,
        start_at: str | None = None,
        end_at: str | None = None,
    ) -> list[dict[str, Any]]:
        query = self.db.table("reviews").select("*").eq("business_profile_id", business_profile_id)
        if start_at:
            query = query.gte("review_created_at", start_at)
        if end_at:
            query = query.lte("review_created_at", end_at)

        result = query.order("review_created_at", desc=True).execute()
        return result.data or []

    async def mark_replied(self, review_id: str):
        now = datetime.now(timezone.utc).isoformat()
        (
            self.db.table("reviews")
            .update({"reply_status": "replied", "response_published_at": now})
            .eq("id", review_id)
            .execute()
        )


class ReviewResponseRepository(BaseRepository):
    """Repository for AI draft and publish tracking."""

    async def create(
        self,
        *,
        review_id: str,
        tone: str,
        draft_text: str,
        edited_text: str | None = None,
        status: str = "draft",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "review_id": review_id,
            "tone": tone,
            "draft_text": draft_text,
            "edited_text": edited_text,
            "status": status,
            "idempotency_key": idempotency_key,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = self.db.table("review_responses").insert(payload).execute()
        return result.data[0] if result.data else {}

    async def get_latest(self, review_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("review_responses")
            .select("*")
            .eq("review_id", review_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> dict[str, Any] | None:
        result = (
            self.db.table("review_responses")
            .select("*")
            .eq("idempotency_key", idempotency_key)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def mark_published(
        self,
        response_id: str,
        final_text: str,
        provider_response: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self.db.table("review_responses")
            .update(
                {
                    "status": "published",
                    "final_text": final_text,
                    "published_at": now,
                    "provider_response": provider_response or {},
                }
            )
            .eq("id", response_id)
            .execute()
        )
        return result.data[0] if result.data else None


class ReviewSentimentRepository(BaseRepository):
    """Repository for review sentiment labels/themes."""

    async def upsert(
        self,
        *,
        review_id: str,
        sentiment_label: str,
        sentiment_score: float,
        themes: list[str],
        model_name: str = "heuristic-v1",
    ) -> dict[str, Any]:
        payload = {
            "review_id": review_id,
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "themes": themes,
            "model_name": model_name,
        }
        result = self.db.table("review_sentiment").upsert(payload, on_conflict="review_id").execute()
        return result.data[0] if result.data else {}

    async def list_by_review_ids(self, review_ids: list[str]) -> list[dict[str, Any]]:
        if not review_ids:
            return []
        result = self.db.table("review_sentiment").select("*").in_("review_id", review_ids).execute()
        return result.data or []


class ReviewSyncJobRepository(BaseRepository):
    """Repository for sync job lifecycle state."""

    async def create(
        self,
        *,
        business_profile_id: str,
        source: str | None,
        mode: str,
        status: str = "queued",
    ) -> dict[str, Any]:
        payload = {
            "business_profile_id": business_profile_id,
            "source": source,
            "mode": mode,
            "status": status,
            "started_at": datetime.now(timezone.utc).isoformat() if status == "running" else None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = self.db.table("review_sync_jobs").insert(payload).execute()
        return result.data[0] if result.data else {}

    async def mark_running(self, job_id: str):
        (
            self.db.table("review_sync_jobs")
            .update(
                {
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "error_code": None,
                    "error_message": None,
                }
            )
            .eq("id", job_id)
            .execute()
        )

    async def mark_finished(
        self,
        job_id: str,
        *,
        status: str,
        records_fetched: int = 0,
        records_upserted: int = 0,
        error_code: str | None = None,
        error_message: str | None = None,
    ):
        (
            self.db.table("review_sync_jobs")
            .update(
                {
                    "status": status,
                    "records_fetched": records_fetched,
                    "records_upserted": records_upserted,
                    "error_code": error_code,
                    "error_message": error_message,
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", job_id)
            .execute()
        )


class ReviewActivityLogRepository(BaseRepository):
    """Repository for auditable review activity events."""

    async def log(
        self,
        *,
        business_profile_id: str,
        action: str,
        review_id: str | None = None,
        source: str | None = None,
        actor_session_id: str | None = None,
        actor_user_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "business_profile_id": business_profile_id,
            "review_id": review_id,
            "source": source,
            "action": action,
            "actor_session_id": actor_session_id,
            "actor_user_id": actor_user_id,
            "details": details or {},
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = self.db.table("review_activity_log").insert(payload).execute()
        return result.data[0] if result.data else {}

    async def count_action_since(self, business_profile_id: str, action: str, since_iso: str) -> int:
        result = (
            self.db.table("review_activity_log")
            .select("id")
            .eq("business_profile_id", business_profile_id)
            .eq("action", action)
            .gte("created_at", since_iso)
            .execute()
        )
        return len(result.data or [])


class ReviewAlertSettingsRepository(BaseRepository):
    """Repository for alert threshold and digest preferences."""

    async def get_or_create(self, business_profile_id: str) -> dict[str, Any]:
        result = (
            self.db.table("review_alert_settings")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]

        created = (
            self.db.table("review_alert_settings")
            .insert({"business_profile_id": business_profile_id})
            .execute()
        )
        return created.data[0] if created.data else {}

    async def update(
        self,
        business_profile_id: str,
        *,
        low_rating_threshold: int,
        instant_low_rating_enabled: bool,
        daily_digest_enabled: bool,
    ) -> dict[str, Any] | None:
        result = (
            self.db.table("review_alert_settings")
            .update(
                {
                    "low_rating_threshold": low_rating_threshold,
                    "instant_low_rating_enabled": instant_low_rating_enabled,
                    "daily_digest_enabled": daily_digest_enabled,
                }
            )
            .eq("business_profile_id", business_profile_id)
            .execute()
        )
        return result.data[0] if result.data else None


class ReviewNotificationRepository(BaseRepository):
    """Repository for review notifications."""

    async def create(
        self,
        *,
        business_profile_id: str,
        notification_type: str,
        title: str,
        body: str,
        review_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "business_profile_id": business_profile_id,
            "review_id": review_id,
            "type": notification_type,
            "title": title,
            "body": body,
            "metadata": metadata or {},
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        result = self.db.table("review_notifications").insert(payload).execute()
        return result.data[0] if result.data else {}

    async def list(
        self,
        business_profile_id: str,
        *,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = (
            self.db.table("review_notifications")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if unread_only:
            query = query.eq("is_read", False)
        result = query.execute()
        return result.data or []

    async def mark_read(self, business_profile_id: str, notification_id: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self.db.table("review_notifications")
            .update({"is_read": True, "read_at": now})
            .eq("id", notification_id)
            .eq("business_profile_id", business_profile_id)
            .execute()
        )
        return bool(result.data)

    async def mark_all_read(self, business_profile_id: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        result = (
            self.db.table("review_notifications")
            .update({"is_read": True, "read_at": now})
            .eq("business_profile_id", business_profile_id)
            .eq("is_read", False)
            .execute()
        )
        return len(result.data or [])

    async def unread_count(self, business_profile_id: str) -> int:
        result = (
            self.db.table("review_notifications")
            .select("id")
            .eq("business_profile_id", business_profile_id)
            .eq("is_read", False)
            .execute()
        )
        return len(result.data or [])
