"""Notification and alert setting service for Reputation Hub."""

from __future__ import annotations

from supabase import Client

from ..repositories.reviews_repository import (
    ReviewAlertSettingsRepository,
    ReviewNotificationRepository,
)
from .review_errors import ValidationFailedError


class ReviewNotificationService:
    """Manages alert settings and notification read state."""

    def __init__(self, db: Client):
        self.settings_repo = ReviewAlertSettingsRepository(db)
        self.notification_repo = ReviewNotificationRepository(db)

    async def get_alert_settings(self, business_profile_id: str) -> dict:
        return await self.settings_repo.get_or_create(business_profile_id)

    async def update_alert_settings(
        self,
        *,
        business_profile_id: str,
        low_rating_threshold: int,
        instant_low_rating_enabled: bool,
        daily_digest_enabled: bool,
    ) -> dict:
        if low_rating_threshold < 1 or low_rating_threshold > 5:
            raise ValidationFailedError("low_rating_threshold must be between 1 and 5")

        existing = await self.settings_repo.get_or_create(business_profile_id)
        updated = await self.settings_repo.update(
            business_profile_id,
            low_rating_threshold=low_rating_threshold,
            instant_low_rating_enabled=instant_low_rating_enabled,
            daily_digest_enabled=daily_digest_enabled,
        )
        return updated or existing

    async def list_notifications(
        self,
        business_profile_id: str,
        *,
        unread_only: bool,
        limit: int,
    ) -> dict:
        notifications = await self.notification_repo.list(
            business_profile_id,
            unread_only=unread_only,
            limit=limit,
        )
        unread_count = await self.notification_repo.unread_count(business_profile_id)
        return {
            "items": notifications,
            "unread_count": unread_count,
        }

    async def mark_read(self, business_profile_id: str, notification_id: str) -> bool:
        return await self.notification_repo.mark_read(business_profile_id, notification_id)

    async def mark_all_read(self, business_profile_id: str) -> int:
        return await self.notification_repo.mark_all_read(business_profile_id)

    async def create_low_rating_notifications(
        self,
        business_profile_id: str,
        reviews: list[dict],
    ) -> int:
        if not reviews:
            return 0

        settings = await self.settings_repo.get_or_create(business_profile_id)
        if not settings.get("instant_low_rating_enabled", True):
            return 0

        threshold = settings.get("low_rating_threshold", 2)
        count = 0
        for review in reviews:
            rating = int(review.get("rating") or 0)
            if rating <= threshold:
                await self.notification_repo.create(
                    business_profile_id=business_profile_id,
                    review_id=review.get("id"),
                    notification_type="low_rating",
                    title=f"Low rating alert ({rating}★)",
                    body=(review.get("content") or "Low rating review received")[:200],
                    metadata={"source": review.get("source"), "rating": rating},
                )
                count += 1
        return count
