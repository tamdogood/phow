import httpx
from typing import Any
from ...core.cache import cached
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

    @cached(ttl=7200, key_prefix="geocode")  # Cache for 2 hours - addresses don't change
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
            logger.info("Geocoding successful", lat=location["lat"], lng=location["lng"])
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": result["formatted_address"],
                "place_id": result.get("place_id"),
            }
        logger.warning("Geocoding failed", status=data["status"])
        return None

    @cached(ttl=1800, key_prefix="nearby")  # Cache for 30 min - businesses change occasionally
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

    @cached(ttl=3600, key_prefix="place_detail")  # Cache for 1 hour - hours/reviews update
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
            "current_opening_hours",
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

    @cached(ttl=1800, key_prefix="popular_times")  # Cache for 30 min
    async def get_popular_times(self, place_id: str) -> dict[str, Any] | None:
        """
        Get popular times (foot traffic) data for a place.
        Note: Popular times data is not directly available via Places API.
        This method returns opening hours as a proxy for business activity patterns.

        For actual popular times, consider using third-party services like:
        - Placer.ai
        - SafeGraph
        - BestTime API
        """
        logger.info("Getting popular times proxy data", place_id=place_id)

        # Get place details with opening hours
        details = await self.get_place_details(place_id)
        if not details:
            return None

        opening_hours = details.get("opening_hours", {})
        current_hours = details.get("current_opening_hours", {})

        result = {
            "place_id": place_id,
            "name": details.get("name"),
            "weekday_text": opening_hours.get("weekday_text", []),
            "open_now": opening_hours.get("open_now"),
            "periods": opening_hours.get("periods", []),
            "note": "Actual popular times data requires third-party API integration",
        }

        # Extract hours by day for analysis
        if opening_hours.get("periods"):
            hours_by_day = self._parse_opening_periods(opening_hours["periods"])
            result["hours_by_day"] = hours_by_day
            result["total_weekly_hours"] = sum(
                h.get("duration_hours", 0) for h in hours_by_day.values()
            )

        return result

    def _parse_opening_periods(self, periods: list[dict]) -> dict[str, Any]:
        """Parse opening periods into hours by day."""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        hours_by_day = {}

        for period in periods:
            open_info = period.get("open", {})
            close_info = period.get("close", {})

            day_idx = open_info.get("day", 0)
            day_name = days[day_idx] if day_idx < len(days) else f"Day {day_idx}"

            open_time = open_info.get("time", "0000")
            close_time = close_info.get("time", "2359")

            # Calculate duration
            try:
                open_hour = int(open_time[:2]) + int(open_time[2:]) / 60
                close_hour = int(close_time[:2]) + int(close_time[2:]) / 60
                if close_hour < open_hour:
                    close_hour += 24  # Handle overnight hours
                duration = close_hour - open_hour
            except (ValueError, IndexError):
                duration = 0

            hours_by_day[day_name] = {
                "open": f"{open_time[:2]}:{open_time[2:]}",
                "close": f"{close_time[:2]}:{close_time[2:]}",
                "duration_hours": round(duration, 1),
            }

        return hours_by_day
