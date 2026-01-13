import httpx
from typing import Any
from ...core.config import get_settings


class GoogleMapsClient:
    """Client for Google Maps API."""

    BASE_URL = "https://maps.googleapis.com/maps/api"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_maps_api_key

    async def geocode(self, address: str) -> dict[str, Any] | None:
        """Convert an address to coordinates."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/geocode/json",
                params={"address": address, "key": self.api_key},
            )
            data = response.json()

            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                location = result["geometry"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "formatted_address": result["formatted_address"],
                    "place_id": result.get("place_id"),
                }
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
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": self.api_key,
        }
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/place/nearbysearch/json",
                params=params,
            )
            data = response.json()

            if data["status"] == "OK":
                return [
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
            return []

    async def get_place_details(self, place_id: str) -> dict[str, Any] | None:
        """Get detailed information about a place."""
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

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/place/details/json",
                params={
                    "place_id": place_id,
                    "fields": ",".join(fields),
                    "key": self.api_key,
                },
            )
            data = response.json()

            if data["status"] == "OK":
                return data["result"]
            return None

    async def analyze_location(self, address: str, business_type: str) -> dict[str, Any]:
        """
        Analyze a location for a specific business type.
        Returns comprehensive data about the area.
        """
        # Geocode the address
        location = await self.geocode(address)
        if not location:
            return {"error": "Could not find the specified address"}

        lat, lng = location["lat"], location["lng"]

        # Get nearby competitors (same business type)
        competitors = await self.nearby_search(lat, lng, radius=1000, keyword=business_type)

        # Get nearby transit
        transit = await self.nearby_search(lat, lng, radius=500, place_type="transit_station")

        # Get nearby restaurants/cafes (foot traffic indicators)
        food_places = await self.nearby_search(lat, lng, radius=500, place_type="restaurant")

        # Get nearby retail (complementary businesses)
        retail = await self.nearby_search(lat, lng, radius=500, place_type="store")

        return {
            "location": location,
            "competitors": competitors[:10],  # Top 10
            "transit_stations": transit[:5],
            "nearby_food": food_places[:10],
            "nearby_retail": retail[:10],
            "analysis_summary": {
                "competitor_count": len(competitors),
                "transit_access": len(transit) > 0,
                "foot_traffic_indicators": len(food_places) + len(retail),
            },
        }
