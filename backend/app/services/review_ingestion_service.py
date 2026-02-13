"""Review sync and ingestion pipeline service."""

from __future__ import annotations

from datetime import datetime, timezone

from supabase import Client

from ..clients.reviews import GoogleReviewsClient, YelpReviewsClient, MetaReviewsClient
from ..core.crypto import get_token_cipher
from ..repositories.reviews_repository import (
    ReviewSourceRepository,
    ReviewRepository,
    ReviewSyncJobRepository,
    ReviewActivityLogRepository,
    ReviewSentimentRepository,
)
from .review_notification_service import ReviewNotificationService
from .review_sentiment_service import ReviewSentimentService
from .review_errors import (
    ValidationFailedError,
    ProviderUnavailableError,
    AuthExpiredError,
    ReviewServiceError,
)

SUPPORTED_SOURCES = {"google", "yelp", "meta"}


class ReviewIngestionService:
    """Runs manual and scheduled review sync jobs."""

    def __init__(self, db: Client):
        self.source_repo = ReviewSourceRepository(db)
        self.review_repo = ReviewRepository(db)
        self.sync_job_repo = ReviewSyncJobRepository(db)
        self.activity_repo = ReviewActivityLogRepository(db)
        self.sentiment_service = ReviewSentimentService(ReviewSentimentRepository(db))
        self.notification_service = ReviewNotificationService(db)

        self.cipher = get_token_cipher()
        self.google_client = GoogleReviewsClient()
        self.yelp_client = YelpReviewsClient()
        self.meta_client = MetaReviewsClient()

    async def sync(
        self,
        *,
        business_profile_id: str,
        source: str | None,
        mode: str,
        actor_session_id: str | None,
        actor_user_id: str | None,
    ) -> dict:
        if source and source not in SUPPORTED_SOURCES:
            raise ValidationFailedError(f"Unsupported source '{source}'")

        connections = await self.source_repo.list_by_profile(business_profile_id)
        by_source = {row["source"]: row for row in connections}

        if source:
            targets = [source]
        else:
            targets = [row["source"] for row in connections if row.get("status") == "connected"]

        if not targets:
            raise ValidationFailedError("No connected sources available for sync")

        total_fetched = 0
        total_upserted = 0
        source_results = []

        for target in targets:
            job = await self.sync_job_repo.create(
                business_profile_id=business_profile_id,
                source=target,
                mode=mode,
                status="running",
            )

            try:
                fetched_reviews = await self._fetch_source_reviews(target, by_source.get(target))
                upserted_rows = await self.review_repo.upsert_many(
                    business_profile_id,
                    by_source.get(target, {}).get("id") if by_source.get(target) else None,
                    fetched_reviews,
                )

                for review in upserted_rows:
                    await self.sentiment_service.classify_and_persist(review)

                notifications_created = await self.notification_service.create_low_rating_notifications(
                    business_profile_id,
                    upserted_rows,
                )

                await self.source_repo.mark_synced(business_profile_id, target)
                await self.sync_job_repo.mark_finished(
                    job["id"],
                    status="success",
                    records_fetched=len(fetched_reviews),
                    records_upserted=len(upserted_rows),
                )

                await self.activity_repo.log(
                    business_profile_id=business_profile_id,
                    source=target,
                    action="sync_completed",
                    actor_session_id=actor_session_id,
                    actor_user_id=actor_user_id,
                    details={
                        "records_fetched": len(fetched_reviews),
                        "records_upserted": len(upserted_rows),
                        "notifications_created": notifications_created,
                    },
                )

                source_results.append(
                    {
                        "source": target,
                        "status": "success",
                        "records_fetched": len(fetched_reviews),
                        "records_upserted": len(upserted_rows),
                    }
                )
                total_fetched += len(fetched_reviews)
                total_upserted += len(upserted_rows)

            except ReviewServiceError as exc:
                await self.sync_job_repo.mark_finished(
                    job["id"],
                    status="failed",
                    error_code=exc.code,
                    error_message=exc.message,
                )
                source_results.append(
                    {
                        "source": target,
                        "status": "failed",
                        "error": {"code": exc.code, "message": exc.message},
                    }
                )
            except Exception as exc:  # Defensive fallback
                await self.sync_job_repo.mark_finished(
                    job["id"],
                    status="failed",
                    error_code="provider_unavailable",
                    error_message=str(exc),
                )
                source_results.append(
                    {
                        "source": target,
                        "status": "failed",
                        "error": {"code": "provider_unavailable", "message": str(exc)},
                    }
                )

        return {
            "mode": mode,
            "total_fetched": total_fetched,
            "total_upserted": total_upserted,
            "sources": source_results,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _fetch_source_reviews(self, source: str, source_connection: dict | None) -> list[dict]:
        if source == "google":
            if not source_connection or source_connection.get("status") != "connected":
                raise ValidationFailedError("Google source is not connected")
            access_token = await self._resolve_google_access_token(source_connection)
            return await self.google_client.list_reviews(access_token)

        if source == "yelp":
            return await self.yelp_client.list_reviews()

        raise ProviderUnavailableError("Meta reviews sync is not available in MVP")

    async def _resolve_google_access_token(self, source_connection: dict) -> str:
        encrypted_access = source_connection.get("access_token_encrypted")
        encrypted_refresh = source_connection.get("refresh_token_encrypted")
        access_token = self.cipher.decrypt(encrypted_access)

        expires_at_str = source_connection.get("token_expires_at")
        if access_token and expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if expires_at > datetime.now(timezone.utc):
                return access_token

        refresh_token = self.cipher.decrypt(encrypted_refresh)
        if not refresh_token:
            raise AuthExpiredError()

        refreshed = await self.google_client.refresh_access_token(refresh_token)
        new_access_token = refreshed.get("access_token")
        if not new_access_token:
            raise AuthExpiredError()

        expires_at_epoch = refreshed.get("expires_at")
        expires_at_iso = (
            datetime.fromtimestamp(expires_at_epoch, tz=timezone.utc).isoformat()
            if expires_at_epoch
            else None
        )

        await self.source_repo.upsert(
            source_connection["business_profile_id"],
            "google",
            status="connected",
            access_token_encrypted=self.cipher.encrypt(new_access_token),
            token_expires_at=expires_at_iso,
            last_error=None,
        )

        return new_access_token
