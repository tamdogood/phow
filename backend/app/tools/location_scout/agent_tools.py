"""LangChain tools for Location Scout agent to interact with Google Maps APIs."""

import asyncio
from typing import Any
from langchain_core.tools import tool
from .google_maps import GoogleMapsClient


# Create a shared client instance
_maps_client: GoogleMapsClient | None = None


def get_maps_client() -> GoogleMapsClient:
    """Get or create the Google Maps client."""
    global _maps_client
    if _maps_client is None:
        _maps_client = GoogleMapsClient()
    return _maps_client


@tool
async def geocode_address(address: str) -> dict[str, Any]:
    """
    Convert an address to geographic coordinates (latitude and longitude).

    Use this tool when you need to:
    - Get the exact location of an address
    - Verify if an address is valid
    - Get the formatted/standardized address

    Args:
        address: The street address to geocode (e.g., "123 Main St, Austin, TX")

    Returns:
        Dictionary with lat, lng, formatted_address, and place_id.
        Returns error message if address cannot be found.
    """
    client = get_maps_client()
    result = await client.geocode(address)
    if result:
        return result
    return {"error": f"Could not find address: {address}"}


@tool
async def search_nearby_places(
    latitude: float,
    longitude: float,
    radius: int = 1000,
    place_type: str | None = None,
    keyword: str | None = None,
) -> list[dict[str, Any]]:
    """
    Search for places near a specific location.

    Use this tool to find:
    - Competitors (use keyword with business type)
    - Transit stations (use place_type="transit_station")
    - Restaurants (use place_type="restaurant")
    - Stores/Retail (use place_type="store")
    - Any type of business or point of interest

    Args:
        latitude: Latitude of the center point
        longitude: Longitude of the center point
        radius: Search radius in meters (default 1000m = 1km)
        place_type: Filter by place type (e.g., "restaurant", "store", "transit_station", "cafe")
        keyword: Search keyword to filter results (e.g., "coffee shop", "bakery", "gym")

    Returns:
        List of places with name, rating, reviews count, vicinity, and other details.
    """
    client = get_maps_client()
    results = await client.nearby_search(
        lat=latitude,
        lng=longitude,
        radius=radius,
        place_type=place_type,
        keyword=keyword,
    )
    return results


@tool
async def get_place_details(place_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific place.

    Use this tool when you need:
    - Business hours/opening times
    - Phone number and website
    - Detailed reviews
    - Price level information

    Args:
        place_id: The Google Place ID of the place to look up

    Returns:
        Detailed place information including name, rating, reviews,
        opening hours, contact info, and more.
    """
    client = get_maps_client()
    result = await client.get_place_details(place_id)
    if result:
        return result
    return {"error": f"Could not find place with ID: {place_id}"}


@tool
async def discover_neighborhood(
    address: str,
    business_type: str | None = None,
) -> dict[str, Any]:
    """
    Comprehensive neighborhood discovery and analysis for a given address.

    Use this tool to get a complete overview of an area, including:
    - Location coordinates and formatted address
    - Competitors (if business_type is provided)
    - Transit access
    - Foot traffic indicators (restaurants, cafes)
    - Nearby retail and complementary businesses

    This is the main tool for analyzing if a location is good for a business.

    Args:
        address: The address to analyze (e.g., "456 Oak Ave, Seattle, WA")
        business_type: Optional type of business for competitor analysis (e.g., "coffee shop", "gym")

    Returns:
        Comprehensive neighborhood data including location, competitors,
        transit stations, nearby food establishments, retail, and summary metrics.
    """
    client = get_maps_client()

    # First geocode the address
    location = await client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Build search tasks for parallel execution
    search_tasks = [
        client.nearby_search(lat, lng, radius=500, place_type="transit_station"),
        client.nearby_search(lat, lng, radius=500, place_type="restaurant"),
        client.nearby_search(lat, lng, radius=500, place_type="store"),
    ]

    # Add competitor search if business type provided
    if business_type:
        search_tasks.insert(0, client.nearby_search(lat, lng, radius=1000, keyword=business_type))

    # Execute all searches in parallel
    search_results = await asyncio.gather(*search_tasks)

    # Unpack results based on whether we searched for competitors
    if business_type:
        competitors, transit_stations, nearby_food, nearby_retail = search_results
    else:
        competitors = []
        transit_stations, nearby_food, nearby_retail = search_results

    results = {
        "location": location,
        "competitors": competitors,
        "transit_stations": transit_stations,
        "nearby_food": nearby_food,
        "nearby_retail": nearby_retail,
    }

    # Limit results
    results["competitors"] = results["competitors"][:10]
    results["transit_stations"] = results["transit_stations"][:5]
    results["nearby_food"] = results["nearby_food"][:10]
    results["nearby_retail"] = results["nearby_retail"][:10]

    # Calculate metrics for enhanced summary
    competitor_count = len(results["competitors"])
    transit_station_count = len(results["transit_stations"])
    foot_traffic_indicators = len(results["nearby_food"]) + len(results["nearby_retail"])

    # Calculate competitor averages
    competitors_with_rating = [c for c in results["competitors"] if c.get("rating")]
    competitor_avg_rating = (
        sum(c["rating"] for c in competitors_with_rating) / len(competitors_with_rating)
        if competitors_with_rating
        else 0
    )

    competitors_with_price = [c for c in results["competitors"] if c.get("price_level")]
    competitor_avg_price = (
        round(sum(c["price_level"] for c in competitors_with_price) / len(competitors_with_price))
        if competitors_with_price
        else 0
    )

    # Calculate transit grade
    transit_grade = (
        "A+"
        if transit_station_count >= 5
        else (
            "A"
            if transit_station_count >= 3
            else "B" if transit_station_count == 2 else "C" if transit_station_count == 1 else "D"
        )
    )

    # Extract unique transit types
    transit_types = list(
        set(
            station.get("types", ["transit"])[0] if station.get("types") else "transit"
            for station in results["transit_stations"]
        )
    )

    # Calculate foot traffic level
    foot_traffic_level = (
        "High"
        if foot_traffic_indicators >= 40
        else "Medium" if foot_traffic_indicators >= 20 else "Low"
    )

    # Calculate location score (weighted: 40% competition, 30% foot traffic, 30% transit)
    competition_score = min(100, (competitor_count / 15) * 100) if competitor_count > 0 else 0
    foot_traffic_score = min(100, (foot_traffic_indicators / 50) * 100)
    transit_score = (transit_station_count / 5) * 100

    location_score = int(
        (competition_score * 0.4) + (foot_traffic_score * 0.3) + (transit_score * 0.3)
    )

    # Calculate location grade
    location_grade = (
        "A+"
        if location_score >= 90
        else (
            "A"
            if location_score >= 85
            else (
                "B+"
                if location_score >= 80
                else (
                    "B"
                    if location_score >= 75
                    else (
                        "C+"
                        if location_score >= 70
                        else "C" if location_score >= 60 else "D" if location_score >= 50 else "F"
                    )
                )
            )
        )
    )

    # Generate key insight
    if location_score >= 85:
        key_insight = f"Excellent location with {foot_traffic_level.lower()} foot traffic and strong transit access ({transit_station_count} stations)"
    elif location_score >= 70:
        key_insight = (
            f"Good location with {foot_traffic_level.lower()} foot traffic and moderate competition"
        )
    elif location_score >= 50:
        key_insight = f"Moderate location with {competitor_count} competitors and {foot_traffic_level.lower()} foot traffic"
    else:
        key_insight = f"Challenging location with limited foot traffic and transit access"

    # Enhanced summary
    results["analysis_summary"] = {
        "competitor_count": competitor_count,
        "transit_access": transit_station_count > 0,
        "foot_traffic_indicators": foot_traffic_indicators,
        "location_score": location_score,
        "location_grade": location_grade,
        "competitor_avg_rating": (
            round(competitor_avg_rating, 1) if competitor_avg_rating > 0 else None
        ),
        "competitor_avg_price": competitor_avg_price if competitor_avg_price > 0 else None,
        "transit_grade": transit_grade,
        "transit_station_count": transit_station_count,
        "transit_types": transit_types,
        "foot_traffic_level": foot_traffic_level,
        "key_insight": key_insight,
    }

    return results


# List of all tools for the agent
LOCATION_SCOUT_TOOLS = [
    geocode_address,
    search_nearby_places,
    get_place_details,
    discover_neighborhood,
]
