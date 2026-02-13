"""Tests for review usage service."""

import pytest

from app.services.review_usage_service import ReviewUsageService
from app.services.review_errors import RateLimitedError


class DummyActivityRepo:
    def __init__(self, count: int):
        self.count = count

    async def count_action_since(self, business_profile_id: str, action: str, since_iso: str) -> int:
        return self.count


@pytest.mark.asyncio
async def test_usage_summary_for_starter_plan():
    service = ReviewUsageService(db=None)  # type: ignore[arg-type]
    service.activity_repo = DummyActivityRepo(count=10)

    usage = await service.get_usage("profile-1", "starter")

    assert usage["monthly_limit"] == 50
    assert usage["used"] == 10
    assert usage["remaining"] == 40
    assert usage["over_limit"] is False


@pytest.mark.asyncio
async def test_over_limit_raises_rate_limited():
    service = ReviewUsageService(db=None)  # type: ignore[arg-type]
    service.activity_repo = DummyActivityRepo(count=50)

    with pytest.raises(RateLimitedError):
        await service.ensure_can_generate("profile-1", "starter")
