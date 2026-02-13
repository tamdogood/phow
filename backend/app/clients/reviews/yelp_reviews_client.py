"""Yelp reviews connector client."""

from __future__ import annotations

import httpx

from ...core.config import get_settings
from ...core.logging import get_logger
from ...services.review_errors import ProviderUnavailableError, RateLimitedError

logger = get_logger("yelp_reviews_client")

YELP_REVIEWS_URL = "https://api.yelp.com/v3/businesses/{business_id}/reviews"


class YelpReviewsClient:
    """Yelp Fusion read-only reviews integration."""

    def __init__(self):
        self.settings = get_settings()

    def get_connection_payload(self) -> dict:
        if not self.settings.yelp_api_key:
            raise ProviderUnavailableError("Yelp API key is not configured")
        return {
            "mode": "api_key",
            "deeplink": "https://biz.yelp.com",
        }

    async def list_reviews(self) -> list[dict]:
        if not self.settings.yelp_api_key:
            raise ProviderUnavailableError("Yelp API key is not configured")
        if not self.settings.yelp_business_id:
            raise ProviderUnavailableError("Yelp business id is not configured")

        url = YELP_REVIEWS_URL.format(business_id=self.settings.yelp_business_id)
        headers = {"Authorization": f"Bearer {self.settings.yelp_api_key}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 429:
            raise RateLimitedError("Yelp API rate limit reached")
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"Yelp reviews fetch failed ({response.status_code})")

        payload = response.json() or {}
        items = payload.get("reviews", [])
        normalized = []
        for item in items:
            user = item.get("user") or {}
            normalized.append(
                {
                    "source": "yelp",
                    "external_review_id": item.get("id"),
                    "external_url": item.get("url"),
                    "reviewer_name": user.get("name"),
                    "rating": int(item.get("rating", 0) or 0),
                    "title": None,
                    "content": item.get("text") or "",
                    "review_created_at": item.get("time_created"),
                    "raw_payload": item,
                }
            )

        logger.info("Fetched Yelp reviews", count=len(normalized))
        return normalized
