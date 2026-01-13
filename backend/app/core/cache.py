import json
import redis.asyncio as redis
from functools import wraps
from typing import Any, Callable
from .config import get_settings


class CacheManager:
    """Redis cache manager with async support."""

    def __init__(self):
        settings = get_settings()
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        self.default_ttl = settings.cache_ttl

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching pattern."""
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.close()


# Global cache instance
_cache: CacheManager | None = None


def get_cache() -> CacheManager:
    """Get or create cache manager instance."""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


def cached(ttl: int | None = None, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=3600, key_prefix="location")
        async def get_location(address: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator
