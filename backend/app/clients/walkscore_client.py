"""Walk Score API client for walkability, transit, and bike scores."""

import httpx
from typing import Any
from ..core.cache import cached
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("walkscore")


class WalkScoreClient:
    """Client for Walk Score API."""

    BASE_URL = "https://api.walkscore.com"
    _client: httpx.AsyncClient | None = None

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.walkscore_api_key

    def _get_client(self) -> httpx.AsyncClient:
        if WalkScoreClient._client is None:
            WalkScoreClient._client = httpx.AsyncClient()
        return WalkScoreClient._client

    @cached(ttl=86400, key_prefix="walkscore")  # Cache for 24 hours - scores rarely change
    async def get_score(
        self, lat: float, lng: float, address: str | None = None
    ) -> dict[str, Any] | None:
        """
        Get Walk Score, Transit Score, and Bike Score for a location.

        Args:
            lat: Latitude
            lng: Longitude
            address: Optional address for better accuracy

        Returns:
            Dict with walkscore, transit_score, bike_score and descriptions
        """
        if not self.api_key:
            logger.warning("Walk Score API key not configured")
            return self._mock_score(lat, lng)

        logger.info("Fetching Walk Score", lat=lat, lng=lng)
        params = {
            "format": "json",
            "lat": lat,
            "lon": lng,
            "wsapikey": self.api_key,
            "transit": 1,
            "bike": 1,
        }
        if address:
            params["address"] = address

        try:
            response = await self._get_client().get(
                f"{self.BASE_URL}/score", params=params, timeout=10.0
            )
            data = response.json()

            if data.get("status") == 1:
                result = {
                    "walkscore": data.get("walkscore"),
                    "walkscore_description": data.get("description"),
                    "transit_score": data.get("transit", {}).get("score"),
                    "transit_description": data.get("transit", {}).get("description"),
                    "bike_score": data.get("bike", {}).get("score"),
                    "bike_description": data.get("bike", {}).get("description"),
                    "updated": data.get("updated"),
                }
                logger.info("Walk Score fetched", walkscore=result["walkscore"])
                return result
            logger.warning("Walk Score API error", status=data.get("status"))
            return None
        except Exception as e:
            logger.error("Walk Score API failed", error=str(e))
            return None

    def _mock_score(self, lat: float, lng: float) -> dict[str, Any]:
        """Return mock scores for development when API key not available."""
        return {
            "walkscore": 75,
            "walkscore_description": "Very Walkable",
            "transit_score": 65,
            "transit_description": "Excellent Transit",
            "bike_score": 70,
            "bike_description": "Very Bikeable",
            "updated": "mock",
        }

    @cached(ttl=86400, key_prefix="walkscore_nearby")
    async def get_nearby_amenities(
        self, lat: float, lng: float, category: str = "all"
    ) -> list[dict[str, Any]]:
        """
        Get nearby amenities that contribute to walk score.

        Categories: restaurant, grocery, shopping, coffee, school, park, etc.
        """
        if not self.api_key:
            return []

        # Note: This requires Walk Score Premium API
        # For now, return empty - can be enhanced with premium access
        logger.info("Nearby amenities not available without premium API")
        return []


_walkscore_client: WalkScoreClient | None = None


def get_walkscore_client() -> WalkScoreClient:
    global _walkscore_client
    if _walkscore_client is None:
        _walkscore_client = WalkScoreClient()
    return _walkscore_client
