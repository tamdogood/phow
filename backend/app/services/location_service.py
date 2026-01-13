from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential
from ..tools.location_scout.google_maps import GoogleMapsClient
from ..core.cache import cached


class LocationService:
    """Service for location-related operations with caching."""

    def __init__(self):
        self.maps_client = GoogleMapsClient()

    @cached(ttl=3600, key_prefix="geocode")
    async def geocode_address(self, address: str) -> dict[str, Any] | None:
        """
        Geocode an address to coordinates.
        Results are cached for 1 hour.
        """
        return await self.maps_client.geocode(address)

    @cached(ttl=1800, key_prefix="nearby")
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_nearby_places(
        self,
        lat: float,
        lng: float,
        radius: int = 1000,
        place_type: str | None = None,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get nearby places with retry logic and caching.
        Results are cached for 30 minutes.
        """
        return await self.maps_client.nearby_search(
            lat=lat,
            lng=lng,
            radius=radius,
            place_type=place_type,
            keyword=keyword,
        )

    @cached(ttl=3600, key_prefix="place_details")
    async def get_place_details(self, place_id: str) -> dict[str, Any] | None:
        """
        Get detailed place information.
        Results are cached for 1 hour.
        """
        return await self.maps_client.get_place_details(place_id)

    async def analyze_location(
        self, address: str, business_type: str
    ) -> dict[str, Any]:
        """
        Comprehensive location analysis with caching.
        This method orchestrates multiple API calls.
        """
        # Geocode the address (cached)
        location = await self.geocode_address(address)
        if not location:
            return {"error": "Could not find the specified address"}

        lat, lng = location["lat"], location["lng"]

        # Parallel API calls for efficiency
        # Get nearby competitors (cached)
        competitors = await self.get_nearby_places(
            lat, lng, radius=1000, keyword=business_type
        )

        # Get nearby transit (cached)
        transit = await self.get_nearby_places(
            lat, lng, radius=500, place_type="transit_station"
        )

        # Get nearby restaurants/cafes (cached)
        food_places = await self.get_nearby_places(
            lat, lng, radius=500, place_type="restaurant"
        )

        # Get nearby retail (cached)
        retail = await self.get_nearby_places(
            lat, lng, radius=500, place_type="store"
        )

        return {
            "location": location,
            "competitors": competitors[:10],
            "transit_stations": transit[:5],
            "nearby_food": food_places[:10],
            "nearby_retail": retail[:10],
            "analysis_summary": {
                "competitor_count": len(competitors),
                "transit_access": len(transit) > 0,
                "foot_traffic_indicators": len(food_places) + len(retail),
            },
        }
