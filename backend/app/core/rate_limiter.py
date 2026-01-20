"""Redis-backed rate limiter with sliding window algorithm."""

import time
import redis.asyncio as redis
from dataclasses import dataclass
from typing import Literal
from .config import get_settings
from .logging import get_logger

logger = get_logger("rate_limiter")

# API rate limit configurations: (requests_per_window, window_seconds)
API_LIMITS: dict[str, tuple[int, int]] = {
    "google": (100, 1),  # 100 QPS
    "yelp": (5000, 86400),  # 5000/day
    "bls": (500, 86400),  # 500/day
    "fred": (120, 60),  # 120/minute (standard FRED limit)
    "census": (500, 86400),  # 500/day estimate
}

ApiName = Literal["google", "yelp", "bls", "fred", "census"]


@dataclass
class QuotaStatus:
    """Rate limit quota status for an API."""

    api_name: str
    remaining: int
    limit: int
    window_seconds: int
    reset_at: float  # Unix timestamp when window resets


class RateLimiter:
    """Redis-backed rate limiter using sliding window algorithm."""

    KEY_PREFIX = "ratelimit"

    def __init__(self):
        settings = get_settings()
        self._redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        self._enabled = True

    def _disable(self, reason: str) -> None:
        if self._enabled:
            logger.warning("Redis unavailable; rate limiting disabled", reason=reason)
        self._enabled = False

    def _key(self, api_name: str) -> str:
        return f"{self.KEY_PREFIX}:{api_name}"

    async def acquire(self, api_name: ApiName, cost: int = 1) -> bool:
        """
        Attempt to acquire rate limit tokens for an API call.

        Args:
            api_name: The API to acquire quota for
            cost: Number of tokens to consume (default 1)

        Returns:
            True if quota acquired, False if quota exhausted
        """
        if not self._enabled:
            return True  # Allow all requests if Redis unavailable

        if api_name not in API_LIMITS:
            logger.warning("Unknown API for rate limiting", api_name=api_name)
            return True

        limit, window = API_LIMITS[api_name]
        key = self._key(api_name)
        now = time.time()
        window_start = now - window

        try:
            pipe = self._redis.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests in window
            pipe.zcard(key)
            # Execute
            results = await pipe.execute()
            current_count = results[1]

            if current_count + cost > limit:
                logger.debug(
                    "Rate limit exceeded",
                    api_name=api_name,
                    current=current_count,
                    limit=limit,
                )
                return False

            # Add new entries for this request
            pipe = self._redis.pipeline()
            for i in range(cost):
                pipe.zadd(key, {f"{now}:{i}": now})
            pipe.expire(key, window)
            await pipe.execute()

            logger.debug(
                "Rate limit acquired",
                api_name=api_name,
                cost=cost,
                remaining=limit - current_count - cost,
            )
            return True

        except Exception as e:
            self._disable(str(e))
            return True  # Allow request if Redis fails

    async def get_quota_status(self, api_name: ApiName) -> QuotaStatus | None:
        """
        Get current quota status for an API.

        Args:
            api_name: The API to check quota for

        Returns:
            QuotaStatus with remaining quota info, or None if API unknown
        """
        if api_name not in API_LIMITS:
            return None

        limit, window = API_LIMITS[api_name]
        now = time.time()

        if not self._enabled:
            return QuotaStatus(
                api_name=api_name,
                remaining=limit,
                limit=limit,
                window_seconds=window,
                reset_at=now + window,
            )

        key = self._key(api_name)
        window_start = now - window

        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zrange(key, 0, 0, withscores=True)
            results = await pipe.execute()

            current_count = results[1]
            oldest_entries = results[2]

            # Calculate reset time based on oldest entry
            if oldest_entries:
                oldest_score = oldest_entries[0][1]
                reset_at = oldest_score + window
            else:
                reset_at = now + window

            return QuotaStatus(
                api_name=api_name,
                remaining=max(0, limit - current_count),
                limit=limit,
                window_seconds=window,
                reset_at=reset_at,
            )

        except Exception as e:
            self._disable(str(e))
            return QuotaStatus(
                api_name=api_name,
                remaining=limit,
                limit=limit,
                window_seconds=window,
                reset_at=now + window,
            )

    async def reset_quota(self, api_name: ApiName) -> bool:
        """
        Reset quota for an API (clear all rate limit entries).

        Args:
            api_name: The API to reset quota for

        Returns:
            True if reset successful, False otherwise
        """
        if api_name not in API_LIMITS:
            return False

        if not self._enabled:
            return True

        key = self._key(api_name)
        try:
            await self._redis.delete(key)
            logger.info("Rate limit reset", api_name=api_name)
            return True
        except Exception as e:
            self._disable(str(e))
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        try:
            await self._redis.close()
        except Exception:
            pass


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
