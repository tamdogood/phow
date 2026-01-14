import httpx
from typing import Any
from ...core.config import get_settings
from ...core.logging import get_logger

logger = get_logger("google_maps")


class GoogleMapsClient:
    """Client for Google Maps API."""

    BASE_URL = "https://maps.googleapis.com/maps/api"
    _client: httpx.AsyncClient | None = None

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_maps_api_key

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create a reusable httpx client."""
        if GoogleMapsClient._client is None:
            GoogleMapsClient._client = httpx.AsyncClient()
        return GoogleMapsClient._client

    async def geocode(self, address: str) -> dict[str, Any] | None:
        """Convert an address to coordinates."""
        logger.info("Geocoding address", address=address)
        response = await self._get_client().get(
            f"{self.BASE_URL}/geocode/json",
            params={"address": address, "key": self.api_key},
        )
        data = response.json()
        logger.debug("Geocode API response", status=data["status"])

        if data["status"] == "OK" and data["results"]:
            result = data["results"][0]
            location = result["geometry"]["location"]
            logger.info(
                "Geocoding successful", lat=location["lat"], lng=location["lng"]
            )
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": result["formatted_address"],
                "place_id": result.get("place_id"),
            }
        logger.warning("Geocoding failed", status=data["status"])
        return None

    async def nearby_search(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        place_type: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for nearby places."""
        logger.info(
            "Nearby search",
            lat=lat,
            lng=lng,
            radius=radius,
            place_type=place_type,
            keyword=keyword,
        )
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": self.api_key,
        }
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword

        response = await self._get_client().get(
            f"{self.BASE_URL}/place/nearbysearch/json",
            params=params,
        )
        data = response.json()
        logger.debug("Nearby search API response", status=data["status"])

        if data["status"] == "OK":
            results = [
                {
                    "name": place["name"],
                    "place_id": place["place_id"],
                    "types": place.get("types", []),
                    "rating": place.get("rating"),
                    "user_ratings_total": place.get("user_ratings_total"),
                    "vicinity": place.get("vicinity"),
                    "price_level": place.get("price_level"),
                    "business_status": place.get("business_status"),
                }
                for place in data["results"]
            ]
            logger.info("Nearby search successful", result_count=len(results))
            return results
        logger.warning("Nearby search returned no results", status=data["status"])
        return []

    async def get_place_details(self, place_id: str) -> dict[str, Any] | None:
        """Get detailed information about a place."""
        logger.info("Getting place details", place_id=place_id)
        fields = [
            "name",
            "rating",
            "reviews",
            "opening_hours",
            "formatted_phone_number",
            "website",
            "price_level",
            "user_ratings_total",
        ]

        response = await self._get_client().get(
            f"{self.BASE_URL}/place/details/json",
            params={
                "place_id": place_id,
                "fields": ",".join(fields),
                "key": self.api_key,
            },
        )
        data = response.json()
        logger.debug("Place details API response", status=data["status"])

        if data["status"] == "OK":
            logger.info("Place details retrieved successfully")
            return data["result"]
        logger.warning("Place details not found", status=data["status"])
        return None
