"""Unit tests for RateLimiter with mocked Redis."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from app.core.rate_limiter import (
    RateLimiter,
    QuotaStatus,
    API_LIMITS,
    get_rate_limiter,
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.pipeline = MagicMock(return_value=AsyncMock())
    return mock


@pytest.fixture
def rate_limiter(mock_redis):
    """Create a RateLimiter with mocked Redis."""
    with patch("app.core.rate_limiter.redis.from_url", return_value=mock_redis):
        limiter = RateLimiter()
        limiter._redis = mock_redis
        return limiter


class TestAcquire:
    """Tests for the acquire method."""

    @pytest.mark.asyncio
    async def test_acquire_success_when_under_limit(self, rate_limiter, mock_redis):
        """Should return True when quota is available."""
        pipe_mock = AsyncMock()
        pipe_mock.execute = AsyncMock(return_value=[None, 50])  # current count = 50
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        result = await rate_limiter.acquire("google", cost=1)

        assert result is True
        # Verify pipeline operations were called
        pipe_mock.zremrangebyscore.assert_called_once()
        pipe_mock.zcard.assert_called_once()

    @pytest.mark.asyncio
    async def test_acquire_failure_when_over_limit(self, rate_limiter, mock_redis):
        """Should return False when quota is exhausted."""
        pipe_mock = AsyncMock()
        # Google limit is 100 QPS, return 100 to exceed
        pipe_mock.execute = AsyncMock(return_value=[None, 100])
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        result = await rate_limiter.acquire("google", cost=1)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_with_cost(self, rate_limiter, mock_redis):
        """Should respect cost parameter when checking limit."""
        pipe_mock = AsyncMock()
        # Google limit is 100, current is 98, cost of 5 should fail
        pipe_mock.execute = AsyncMock(return_value=[None, 98])
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        result = await rate_limiter.acquire("google", cost=5)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_unknown_api_returns_true(self, rate_limiter):
        """Should return True for unknown API names (allow by default)."""
        result = await rate_limiter.acquire("unknown_api", cost=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_returns_true_when_redis_disabled(self, rate_limiter):
        """Should return True when Redis is disabled."""
        rate_limiter._enabled = False
        result = await rate_limiter.acquire("google", cost=1)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_handles_redis_error_gracefully(self, rate_limiter, mock_redis):
        """Should return True and disable when Redis fails."""
        pipe_mock = AsyncMock()
        pipe_mock.execute = AsyncMock(side_effect=Exception("Redis connection error"))
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        result = await rate_limiter.acquire("google", cost=1)

        assert result is True  # Graceful fallback
        assert rate_limiter._enabled is False


class TestGetQuotaStatus:
    """Tests for the get_quota_status method."""

    @pytest.mark.asyncio
    async def test_get_quota_status_returns_correct_status(self, rate_limiter, mock_redis):
        """Should return accurate quota status."""
        now = time.time()
        pipe_mock = AsyncMock()
        pipe_mock.execute = AsyncMock(
            return_value=[
                None,  # zremrangebyscore result
                30,  # zcard result (30 requests used)
                [("entry", now - 0.5)],  # oldest entry
            ]
        )
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        status = await rate_limiter.get_quota_status("google")

        assert status is not None
        assert status.api_name == "google"
        assert status.remaining == 70  # 100 - 30
        assert status.limit == 100
        assert status.window_seconds == 1

    @pytest.mark.asyncio
    async def test_get_quota_status_unknown_api_returns_none(self, rate_limiter):
        """Should return None for unknown API."""
        status = await rate_limiter.get_quota_status("unknown_api")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_quota_status_when_disabled(self, rate_limiter):
        """Should return full quota when Redis is disabled."""
        rate_limiter._enabled = False

        status = await rate_limiter.get_quota_status("google")

        assert status is not None
        assert status.remaining == 100
        assert status.limit == 100

    @pytest.mark.asyncio
    async def test_get_quota_status_handles_redis_error(self, rate_limiter, mock_redis):
        """Should return full quota when Redis fails."""
        pipe_mock = AsyncMock()
        pipe_mock.execute = AsyncMock(side_effect=Exception("Redis error"))
        mock_redis.pipeline = MagicMock(return_value=pipe_mock)

        status = await rate_limiter.get_quota_status("yelp")

        assert status is not None
        assert status.remaining == 5000  # Yelp daily limit
        assert status.limit == 5000


class TestResetQuota:
    """Tests for the reset_quota method."""

    @pytest.mark.asyncio
    async def test_reset_quota_success(self, rate_limiter, mock_redis):
        """Should successfully reset quota."""
        mock_redis.delete = AsyncMock()

        result = await rate_limiter.reset_quota("google")

        assert result is True
        mock_redis.delete.assert_called_once_with("ratelimit:google")

    @pytest.mark.asyncio
    async def test_reset_quota_unknown_api_returns_false(self, rate_limiter):
        """Should return False for unknown API."""
        result = await rate_limiter.reset_quota("unknown_api")
        assert result is False

    @pytest.mark.asyncio
    async def test_reset_quota_when_disabled(self, rate_limiter):
        """Should return True when Redis is disabled."""
        rate_limiter._enabled = False
        result = await rate_limiter.reset_quota("google")
        assert result is True

    @pytest.mark.asyncio
    async def test_reset_quota_handles_redis_error(self, rate_limiter, mock_redis):
        """Should return False when Redis fails."""
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))

        result = await rate_limiter.reset_quota("google")

        assert result is False
        assert rate_limiter._enabled is False


class TestAPILimits:
    """Tests for API limit configurations."""

    def test_google_limit_is_100_qps(self):
        """Google should have 100 QPS limit."""
        limit, window = API_LIMITS["google"]
        assert limit == 100
        assert window == 1

    def test_yelp_limit_is_5000_per_day(self):
        """Yelp should have 5000/day limit."""
        limit, window = API_LIMITS["yelp"]
        assert limit == 5000
        assert window == 86400

    def test_bls_limit_is_500_per_day(self):
        """BLS should have 500/day limit."""
        limit, window = API_LIMITS["bls"]
        assert limit == 500
        assert window == 86400


class TestGlobalInstance:
    """Tests for the global rate limiter instance."""

    def test_get_rate_limiter_returns_instance(self):
        """Should return a RateLimiter instance."""
        with patch("app.core.rate_limiter.redis.from_url"):
            limiter = get_rate_limiter()
            assert isinstance(limiter, RateLimiter)

    def test_get_rate_limiter_returns_same_instance(self):
        """Should return the same instance on subsequent calls."""
        with patch("app.core.rate_limiter.redis.from_url"):
            # Reset global state
            import app.core.rate_limiter as module

            module._rate_limiter = None

            limiter1 = get_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is limiter2


class TestQuotaStatusDataclass:
    """Tests for QuotaStatus dataclass."""

    def test_quota_status_fields(self):
        """Should have correct fields."""
        status = QuotaStatus(
            api_name="google",
            remaining=50,
            limit=100,
            window_seconds=1,
            reset_at=1234567890.0,
        )
        assert status.api_name == "google"
        assert status.remaining == 50
        assert status.limit == 100
        assert status.window_seconds == 1
        assert status.reset_at == 1234567890.0


class TestClose:
    """Tests for the close method."""

    @pytest.mark.asyncio
    async def test_close_success(self, rate_limiter, mock_redis):
        """Should close Redis connection."""
        mock_redis.close = AsyncMock()
        await rate_limiter.close()
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_error(self, rate_limiter, mock_redis):
        """Should handle close errors gracefully."""
        mock_redis.close = AsyncMock(side_effect=Exception("Close error"))
        # Should not raise
        await rate_limiter.close()
