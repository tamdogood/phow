"""Usage metering service for AI draft generation."""

from __future__ import annotations

from datetime import datetime, timezone

from supabase import Client

from ..core.config import get_settings
from ..repositories.reviews_repository import ReviewActivityLogRepository
from .review_errors import RateLimitedError


PLAN_LIMITS = {
    "starter": 50,
    "growth": 150,
    "scale": 300,
}


class ReviewUsageService:
    """Tracks monthly draft-generation usage against plan limits."""

    def __init__(self, db: Client):
        self.settings = get_settings()
        self.activity_repo = ReviewActivityLogRepository(db)

    async def get_usage(self, business_profile_id: str, plan: str | None = None) -> dict:
        normalized_plan = (plan or self.settings.reputation_default_plan or "starter").lower()
        monthly_limit = PLAN_LIMITS.get(normalized_plan, PLAN_LIMITS["starter"])

        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc).isoformat()

        used = await self.activity_repo.count_action_since(
            business_profile_id,
            action="draft_generated",
            since_iso=month_start,
        )

        remaining = max(0, monthly_limit - used)
        return {
            "plan": normalized_plan,
            "monthly_limit": monthly_limit,
            "used": used,
            "remaining": remaining,
            "over_limit": used >= monthly_limit,
            "period_start": month_start,
        }

    async def ensure_can_generate(self, business_profile_id: str, plan: str | None = None):
        usage = await self.get_usage(business_profile_id, plan)
        if usage["over_limit"]:
            raise RateLimitedError(
                f"Draft generation limit reached for plan '{usage['plan']}'. Upgrade plan or wait for reset"
            )
