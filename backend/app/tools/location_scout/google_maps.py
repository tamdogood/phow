import re
import httpx
from typing import Any
from ...core.cache import cached
from ...core.config import get_settings
from ...core.logging import get_logger

logger = get_logger("google_maps")


class GoogleMapsClient:
    """Client for Google Maps API."""

    BASE_URL = "https://maps.googleapis.com/maps/api"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_maps_api_key

    @cached(ttl=7200, key_prefix="geocode")  # Cache for 2 hours - addresses don't change
    async def geocode(self, address: str) -> dict[str, Any] | None:
        """Convert an address to coordinates."""
        logger.info("Geocoding address", address=address)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
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

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
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
                    "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                    "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                    "price_level": place.get("price_level"),
                    "business_status": place.get("business_status"),
                }
                for place in data["results"]
            ]
            logger.info("Nearby search successful", result_count=len(results))
            return results
        logger.warning("Nearby search returned no results", status=data["status"])
        return []

    @cached(ttl=7200, key_prefix="find_place")
    async def find_place(self, query: str, lat: float, lng: float) -> dict[str, Any] | None:
        """Find a specific business by name near a location. Returns the place_id of the listing."""
        logger.info("Find place", query=query, lat=lat, lng=lng)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/place/findplacefromtext/json",
                params={
                    "input": query,
                    "inputtype": "textquery",
                    "locationbias": f"circle:5000@{lat},{lng}",
                    "fields": "place_id,name,formatted_address",
                    "key": self.api_key,
                },
            )
        data = response.json()
        if data.get("status") == "OK" and data.get("candidates"):
            candidate = data["candidates"][0]
            logger.info(
                "Find place successful", place_id=candidate["place_id"], name=candidate.get("name")
            )
            return candidate
        logger.warning("Find place failed", status=data.get("status"), query=query)
        return None

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

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
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

    async def resolve_maps_url(self, url: str) -> dict[str, Any] | None:
        """Resolve a Google Maps URL (including short URLs) to place details.

        Follows redirects, extracts place name + coordinates, and calls find_place.
        """
        logger.info("Resolving Google Maps URL", url=url)
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url)
                expanded = str(response.url)
        except Exception as e:
            logger.warning("Failed to follow Maps URL", url=url, error=str(e))
            return None

        # Try extracting coordinates from the expanded URL
        # Patterns: /@lat,lng  or !3dlat!4dlng or center=lat,lng
        coord_match = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", expanded)
        if not coord_match:
            coord_match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", expanded)
        if not coord_match:
            logger.warning("Could not extract coordinates from Maps URL", expanded=expanded)
            return None

        lat, lng = float(coord_match.group(1)), float(coord_match.group(2))

        # Try to extract place name from /place/NAME/ pattern
        place_match = re.search(r"/place/([^/@]+)", expanded)
        query = place_match.group(1).replace("+", " ") if place_match else ""

        if query:
            found = await self.find_place(query, lat, lng)
            if found:
                return {**found, "lat": lat, "lng": lng}

        # Fallback: reverse geocode or return coordinates
        return {"lat": lat, "lng": lng, "place_id": None, "name": query or None}

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
