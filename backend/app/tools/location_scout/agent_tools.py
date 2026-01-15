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

    # Add summary
    results["analysis_summary"] = {
        "competitor_count": len(results["competitors"]),
        "transit_access": len(results["transit_stations"]) > 0,
        "foot_traffic_indicators": len(results["nearby_food"]) + len(results["nearby_retail"]),
    }

    return results


# List of all tools for the agent
LOCATION_SCOUT_TOOLS = [
    geocode_address,
    search_nearby_places,
    get_place_details,
    discover_neighborhood,
]
