"""Yelp Fusion API client for business and review data."""

import os
import httpx
from typing import Any
from ...core.logging import get_logger
from ...core.cache import cached

logger = get_logger("yelp_client")

YELP_API_BASE = "https://api.yelp.com/v3"


class YelpClient:
    """Client for Yelp Fusion API."""

    def __init__(self):
        self.api_key = os.getenv("YELP_API_KEY", "")
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
        )
        self.enabled = bool(self.api_key)
        if not self.enabled:
            logger.warning("Yelp API key not configured - Yelp features disabled")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @cached(ttl=3600, key_prefix="yelp_search")
    async def search_businesses(
        self,
        term: str,
        latitude: float,
        longitude: float,
        radius: int = 1000,
        limit: int = 20,
        sort_by: str = "distance",
    ) -> list[dict[str, Any]]:
        """
        Search for businesses on Yelp.

        Args:
            term: Search term (e.g., "coffee shop")
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters (max 40000)
            limit: Max results (max 50)
            sort_by: Sort order ('best_match', 'rating', 'review_count', 'distance')

        Returns:
            List of business data
        """
        if not self.enabled:
            return []

        try:
            response = await self.client.get(
                f"{YELP_API_BASE}/businesses/search",
                params={
                    "term": term,
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": min(radius, 40000),
                    "limit": min(limit, 50),
                    "sort_by": sort_by,
                },
            )
            response.raise_for_status()
            data = response.json()
            businesses = data.get("businesses", [])

            logger.info(
                "Yelp search completed",
                term=term,
                results=len(businesses),
            )

            return [
                {
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "rating": b.get("rating"),
                    "review_count": b.get("review_count"),
                    "price": b.get("price"),  # $, $$, $$$, $$$$
                    "address": ", ".join(b.get("location", {}).get("display_address", [])),
                    "phone": b.get("display_phone"),
                    "categories": [c.get("title") for c in b.get("categories", [])],
                    "distance_meters": b.get("distance"),
                    "is_closed": b.get("is_closed"),
                    "url": b.get("url"),
                    "image_url": b.get("image_url"),
                    "coordinates": {
                        "lat": b.get("coordinates", {}).get("latitude"),
                        "lng": b.get("coordinates", {}).get("longitude"),
                    },
                }
                for b in businesses
            ]

        except httpx.HTTPError as e:
            logger.error("Yelp search failed", error=str(e))
            return []

    @cached(ttl=3600, key_prefix="yelp_business")
    async def get_business_details(self, business_id: str) -> dict[str, Any] | None:
        """
        Get detailed information about a business.

        Args:
            business_id: Yelp business ID

        Returns:
            Business details including hours, photos, etc.
        """
        if not self.enabled:
            return None

        try:
            response = await self.client.get(f"{YELP_API_BASE}/businesses/{business_id}")
            response.raise_for_status()
            b = response.json()

            # Extract hours
            hours = []
            for day_hours in b.get("hours", [{}])[0].get("open", []):
                hours.append(
                    {
                        "day": day_hours.get("day"),
                        "start": day_hours.get("start"),
                        "end": day_hours.get("end"),
                    }
                )

            return {
                "id": b.get("id"),
                "name": b.get("name"),
                "rating": b.get("rating"),
                "review_count": b.get("review_count"),
                "price": b.get("price"),
                "address": ", ".join(b.get("location", {}).get("display_address", [])),
                "phone": b.get("display_phone"),
                "categories": [c.get("title") for c in b.get("categories", [])],
                "is_closed": b.get("is_closed"),
                "url": b.get("url"),
                "photos": b.get("photos", [])[:5],
                "hours": hours,
                "is_open_now": b.get("hours", [{}])[0].get("is_open_now"),
                "transactions": b.get("transactions", []),  # pickup, delivery, etc.
            }

        except httpx.HTTPError as e:
            logger.error("Yelp business details failed", error=str(e), business_id=business_id)
            return None

    @cached(ttl=1800, key_prefix="yelp_reviews")  # Cache for 30 min
    async def get_business_reviews(self, business_id: str, limit: int = 3) -> list[dict[str, Any]]:
        """
        Get reviews for a business.

        Note: Yelp API only returns up to 3 reviews.

        Args:
            business_id: Yelp business ID
            limit: Max reviews (max 3 due to API limit)

        Returns:
            List of reviews
        """
        if not self.enabled:
            return []

        try:
            response = await self.client.get(
                f"{YELP_API_BASE}/businesses/{business_id}/reviews",
                params={"limit": min(limit, 3)},
            )
            response.raise_for_status()
            data = response.json()

            return [
                {
                    "id": r.get("id"),
                    "rating": r.get("rating"),
                    "text": r.get("text"),
                    "time_created": r.get("time_created"),
                    "user": {
                        "name": r.get("user", {}).get("name"),
                        "image_url": r.get("user", {}).get("image_url"),
                    },
                }
                for r in data.get("reviews", [])
            ]

        except httpx.HTTPError as e:
            logger.error("Yelp reviews failed", error=str(e), business_id=business_id)
            return []


# Singleton instance
_yelp_client: YelpClient | None = None


def get_yelp_client() -> YelpClient:
    """Get or create the Yelp client."""
    global _yelp_client
    if _yelp_client is None:
        _yelp_client = YelpClient()
    return _yelp_client
