"""LangChain tools for RAG-based location intelligence retrieval."""

from typing import Any
from langchain_core.tools import tool
from ...clients import (
    get_walkscore_client,
    get_trends_client,
    get_crime_client,
    get_health_inspection_client,
    get_menu_scraper,
)
from ...core.logging import get_logger

logger = get_logger("rag_tools")


@tool
async def search_location_intelligence(
    query: str,
    latitude: float,
    longitude: float,
    city: str,
    data_types: list[str] | None = None,
) -> str:
    """
    Search our location intelligence database for business insights.

    Use this tool to find relevant data about a location including crime rates,
    health inspections, foot traffic, pricing benchmarks, and search trends.

    Args:
        query: Natural language query (e.g., "crime statistics", "restaurant health scores")
        latitude: Location latitude
        longitude: Location longitude
        city: City name
        data_types: Optional filter - 'crime', 'health', 'walkscore', 'trends', 'menu'

    Returns:
        Relevant location intelligence data as formatted text
    """
    logger.info("Location intelligence search", query=query, city=city)

    results = []

    # Determine which data sources to query based on query content
    query_lower = query.lower()

    if not data_types or "walkscore" in (data_types or []) or any(
        kw in query_lower for kw in ["walk", "transit", "bike", "walkable", "accessibility"]
    ):
        walk_data = await get_walkscore_client().get_score(latitude, longitude)
        if walk_data:
            results.append(f"**Walk Score**: {walk_data.get('walkscore')} ({walk_data.get('walkscore_description')})")
            results.append(f"**Transit Score**: {walk_data.get('transit_score')} ({walk_data.get('transit_description')})")
            results.append(f"**Bike Score**: {walk_data.get('bike_score')} ({walk_data.get('bike_description')})")

    if not data_types or "crime" in (data_types or []) or any(
        kw in query_lower for kw in ["crime", "safety", "safe", "dangerous", "security"]
    ):
        crime_data = await get_crime_client().get_crimes_nearby(latitude, longitude, city)
        if crime_data.get("total_crimes", 0) > 0 or crime_data.get("safety_score"):
            results.append(f"\n**Crime Data** ({city}):")
            results.append(f"- Total crimes (90 days): {crime_data.get('total_crimes', 'N/A')}")
            results.append(f"- Safety score: {crime_data.get('safety_score', 'N/A')}/100")
            results.append(f"- Crime rate: {crime_data.get('crime_rate', 'unknown')}")
            results.append(f"- Recommendation: {crime_data.get('recommendation', 'N/A')}")

    if not data_types or "health" in (data_types or []) or any(
        kw in query_lower for kw in ["health", "inspection", "hygiene", "sanitary", "restaurant"]
    ):
        health_data = await get_health_inspection_client().get_inspections_nearby(latitude, longitude, city)
        if health_data.get("total_restaurants", 0) > 0:
            results.append(f"\n**Health Inspections** ({city}):")
            results.append(f"- Restaurants analyzed: {health_data.get('total_restaurants')}")
            results.append(f"- Average score: {health_data.get('avg_score', 'N/A')}")
            results.append(f"- Health rating: {health_data.get('health_rating', 'unknown')}")
            results.append(f"- Insight: {health_data.get('insight', 'N/A')}")

    if not results:
        return f"No specific data found for this location. Try searching for 'crime safety', 'walkability', or 'health inspections' in {city}."

    return "\n".join(results)


@tool
async def get_location_scores(latitude: float, longitude: float, address: str | None = None) -> str:
    """
    Get walkability, transit, and bike scores for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        address: Optional address for better accuracy

    Returns:
        Walk Score, Transit Score, and Bike Score with descriptions
    """
    logger.info("Getting location scores", lat=latitude, lng=longitude)

    client = get_walkscore_client()
    scores = await client.get_score(latitude, longitude, address)

    if not scores:
        return "Unable to retrieve walkability scores for this location."

    return (
        f"**Walkability Analysis**\n"
        f"- Walk Score: {scores.get('walkscore', 'N/A')} - {scores.get('walkscore_description', 'N/A')}\n"
        f"- Transit Score: {scores.get('transit_score', 'N/A')} - {scores.get('transit_description', 'N/A')}\n"
        f"- Bike Score: {scores.get('bike_score', 'N/A')} - {scores.get('bike_description', 'N/A')}\n\n"
        f"Higher scores indicate better accessibility for customers without cars."
    )


@tool
async def get_crime_data(
    latitude: float,
    longitude: float,
    city: str,
    radius_meters: int = 1000,
) -> str:
    """
    Get crime statistics and safety analysis for a location.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        city: City name (required for data lookup)
        radius_meters: Search radius in meters (default 1000m / ~0.6 miles)

    Returns:
        Crime statistics, safety score, and business recommendations
    """
    logger.info("Getting crime data", lat=latitude, lng=longitude, city=city)

    client = get_crime_client()

    # Check if city is supported
    supported = client.get_supported_cities()
    if not any(s in city.lower() for s in supported):
        return f"Crime data not available for {city}. Supported cities: {', '.join(supported[:10])}..."

    data = await client.get_crimes_nearby(latitude, longitude, city, radius_meters)

    if data.get("crime_rate") == "unknown":
        return f"Unable to retrieve crime data for this location in {city}."

    result = [
        f"**Crime Analysis for {city}** (within {radius_meters}m radius)\n",
        f"- Total incidents (90 days): {data.get('total_crimes', 'N/A')}",
        f"- Safety Score: {data.get('safety_score', 'N/A')}/100",
        f"- Crime Rate: {data.get('crime_rate', 'N/A')}",
        f"- Violent Crime: {data.get('violent_crime_pct', 'N/A')}%",
        f"- Crimes per sq km: {data.get('crimes_per_sq_km', 'N/A')}",
    ]

    if data.get("by_type"):
        result.append("\n**Top Crime Types:**")
        for crime_type, count in list(data["by_type"].items())[:5]:
            result.append(f"  - {crime_type}: {count}")

    result.append(f"\n**Recommendation:** {data.get('recommendation', 'N/A')}")

    return "\n".join(result)


@tool
async def get_health_inspections(
    latitude: float,
    longitude: float,
    city: str,
    radius_meters: int = 1000,
) -> str:
    """
    Get health inspection scores for restaurants near a location.
    Critical for F&B businesses to understand local hygiene standards.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        city: City name
        radius_meters: Search radius in meters

    Returns:
        Average health scores, grade distribution, and competitor hygiene insights
    """
    logger.info("Getting health inspections", lat=latitude, lng=longitude, city=city)

    client = get_health_inspection_client()

    supported = client.get_supported_cities()
    if not any(s in city.lower() for s in supported):
        return f"Health inspection data not available for {city}. Supported: {', '.join(supported)}."

    data = await client.get_inspections_nearby(latitude, longitude, city, radius_meters)

    if data.get("total_restaurants", 0) == 0:
        return f"No health inspection data found for restaurants in this area of {city}."

    result = [
        f"**Health Inspection Analysis for {city}** (within {radius_meters}m)\n",
        f"- Restaurants Analyzed: {data.get('total_restaurants')}",
        f"- Average Score: {data.get('avg_score', 'N/A')}",
        f"- Overall Rating: {data.get('health_rating', 'unknown')}",
    ]

    if data.get("grade_distribution"):
        result.append("\n**Grade Distribution:**")
        for grade, count in data["grade_distribution"].items():
            result.append(f"  - Grade {grade}: {count} restaurants")

    result.append(f"\n**Insight:** {data.get('insight', 'N/A')}")

    # Show top restaurants
    if data.get("restaurants"):
        result.append("\n**Sample Restaurants:**")
        for r in data["restaurants"][:5]:
            score_str = f"Score: {r.get('score')}" if r.get("score") else f"Grade: {r.get('grade', 'N/A')}"
            result.append(f"  - {r.get('name', 'Unknown')}: {score_str}")

    return "\n".join(result)


@tool
async def get_pricing_benchmarks(
    business_type: str,
    city: str,
    items: list[str] | None = None,
) -> str:
    """
    Get menu pricing benchmarks for a business type in a city.
    Helps F&B businesses understand local price points.

    Args:
        business_type: Type of business (coffee_shop, pizza, burger, sushi, mexican)
        city: City name
        items: Optional specific items to look up

    Returns:
        Price ranges and benchmarks for the business type
    """
    logger.info("Getting pricing benchmarks", business_type=business_type, city=city)

    scraper = get_menu_scraper()
    data = await scraper.get_price_comparison(business_type, city, items)

    if not data.get("benchmarks"):
        return f"No pricing benchmarks available for {business_type} in {city}."

    result = [
        f"**Pricing Benchmarks: {business_type.replace('_', ' ').title()} in {city}**\n",
        f"Cost multiplier vs national average: {data.get('cost_multiplier', 1.0):.2f}x\n",
    ]

    for item, prices in data.get("benchmarks", {}).items():
        item_name = item.replace("_", " ").title()
        result.append(
            f"- **{item_name}**: ${prices['low']:.2f} - ${prices['high']:.2f} "
            f"(avg ${prices['avg']:.2f})"
        )

    result.append(f"\n*{data.get('note', '')}*")

    return "\n".join(result)


@tool
async def get_search_trends(
    keywords: list[str],
    city: str | None = None,
) -> str:
    """
    Get Google search trends for keywords, optionally filtered by city.
    Useful for understanding demand and market interest.

    Args:
        keywords: List of search terms to analyze (max 5)
        city: Optional city to filter trends

    Returns:
        Search interest over time and related rising queries
    """
    logger.info("Getting search trends", keywords=keywords, city=city)

    client = get_trends_client()

    # Get interest over time
    interest_data = await client.get_interest_over_time(keywords[:5], city)

    if interest_data.get("error"):
        return f"Unable to fetch trends: {interest_data.get('error')}"

    result = [f"**Search Trends: {', '.join(keywords)}**"]

    if city:
        result.append(f"Location: {city}")
    result.append(f"Timeframe: {interest_data.get('timeframe', '12 months')}\n")

    # Get latest interest scores
    if interest_data.get("data"):
        result.append("**Current Interest (0-100 scale):**")
        latest = interest_data["data"][-1] if interest_data["data"] else {}
        for kw in keywords:
            score = latest.get(kw, "N/A")
            result.append(f"  - {kw}: {score}")

    # Get related queries for the first keyword
    if keywords:
        related = await client.get_related_queries(keywords[0], city)
        if related.get("rising"):
            result.append(f"\n**Rising Related Searches for '{keywords[0]}':**")
            for q in related["rising"][:5]:
                query = q.get("query", "N/A")
                value = q.get("value", "N/A")
                result.append(f"  - {query}: {value}")

    return "\n".join(result)


# Convenience list of all RAG tools for agent registration
RAG_TOOLS = [
    search_location_intelligence,
    get_location_scores,
    get_crime_data,
    get_health_inspections,
    get_pricing_benchmarks,
    get_search_trends,
]
