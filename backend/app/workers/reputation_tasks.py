"""Celery tasks for Reputation Hub sync and token maintenance."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from .celery_app import celery_app
from ..api.deps import get_supabase
from ..core.crypto import get_token_cipher
from ..core.logging import get_logger
from ..repositories.reviews_repository import ReviewSourceRepository
from ..services.review_ingestion_service import ReviewIngestionService
from ..clients.reviews import GoogleReviewsClient

logger = get_logger("reputation_tasks")


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def sync_reviews_all_profiles() -> dict[str, Any]:
    """Sync connected review sources for all business profiles."""

    async def _run() -> dict[str, Any]:
        db = get_supabase()
        result = db.table("business_profiles").select("id").execute()
        profiles = result.data or []

        sync_service = ReviewIngestionService(db)

        summary = {
            "profiles_processed": 0,
            "profiles_succeeded": 0,
            "profiles_failed": 0,
            "errors": [],
        }

        for profile in profiles:
            profile_id = profile["id"]
            summary["profiles_processed"] += 1
            try:
                await sync_service.sync(
                    business_profile_id=profile_id,
                    source=None,
                    mode="scheduled",
                    actor_session_id=None,
                    actor_user_id=None,
                )
                summary["profiles_succeeded"] += 1
            except Exception as exc:
                summary["profiles_failed"] += 1
                summary["errors"].append({"business_profile_id": profile_id, "error": str(exc)})

        return summary

    return run_async(_run())


@celery_app.task
def refresh_google_tokens() -> dict[str, Any]:
    """Refresh expiring Google OAuth access tokens for connected sources."""

    async def _run() -> dict[str, Any]:
        db = get_supabase()
        source_repo = ReviewSourceRepository(db)
        cipher = get_token_cipher()
        google_client = GoogleReviewsClient()

        cutoff = datetime.now(timezone.utc) + timedelta(minutes=10)
        result = (
            db.table("review_sources")
            .select("*")
            .eq("source", "google")
            .eq("status", "connected")
            .not_.is_("refresh_token_encrypted", "null")
            .execute()
        )
        sources = result.data or []

        refreshed = 0
        failed = 0

        for source in sources:
            expires_at_raw = source.get("token_expires_at")
            if not expires_at_raw:
                continue

            try:
                expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            except Exception:
                continue

            if expires_at > cutoff:
                continue

            refresh_token = cipher.decrypt(source.get("refresh_token_encrypted"))
            if not refresh_token:
                failed += 1
                continue

            try:
                new_tokens = await google_client.refresh_access_token(refresh_token)
                new_access_token = new_tokens.get("access_token")
                expires_epoch = new_tokens.get("expires_at")
                new_expiry = (
                    datetime.fromtimestamp(expires_epoch, tz=timezone.utc).isoformat()
                    if expires_epoch
                    else None
                )

                await source_repo.upsert(
                    source["business_profile_id"],
                    "google",
                    status="connected",
                    access_token_encrypted=cipher.encrypt(new_access_token),
                    token_expires_at=new_expiry,
                    last_error=None,
                )
                refreshed += 1
            except Exception as exc:
                failed += 1
                logger.warning("Failed to refresh Google token", source_id=source["id"], error=str(exc))

        return {"refreshed": refreshed, "failed": failed, "checked": len(sources)}

    return run_async(_run())
