"""LangChain tools for Market Validator agent."""

import asyncio
from typing import Any
from langchain_core.tools import tool
from .census_client import get_census_client
from ..location_scout.google_maps import GoogleMapsClient
from ...core.logging import get_logger

logger = get_logger("market_validator.tools")

# Shared clients
_maps_client: GoogleMapsClient | None = None


def get_maps_client() -> GoogleMapsClient:
    """Get or create the Google Maps client."""
    global _maps_client
    if _maps_client is None:
        _maps_client = GoogleMapsClient()
    return _maps_client


# Business type to target demographic mappings
BUSINESS_DEMOGRAPHICS = {
    "coffee_shop": {
        "ideal_age": "18-45",
        "ideal_income": "middle_to_upper",
        "ideal_education": "college_educated",
        "foot_traffic_importance": "high",
    },
    "restaurant": {
        "ideal_age": "25-55",
        "ideal_income": "middle_to_upper",
        "ideal_education": "any",
        "foot_traffic_importance": "high",
    },
    "gym": {
        "ideal_age": "18-45",
        "ideal_income": "middle_to_upper",
        "ideal_education": "any",
        "foot_traffic_importance": "medium",
    },
    "retail": {
        "ideal_age": "25-55",
        "ideal_income": "middle",
        "ideal_education": "any",
        "foot_traffic_importance": "high",
    },
    "salon": {
        "ideal_age": "18-55",
        "ideal_income": "middle",
        "ideal_education": "any",
        "foot_traffic_importance": "medium",
    },
    "daycare": {
        "ideal_age": "25-45",
        "ideal_income": "middle_to_upper",
        "ideal_education": "any",
        "foot_traffic_importance": "low",
    },
    "pet_store": {
        "ideal_age": "25-55",
        "ideal_income": "middle_to_upper",
        "ideal_education": "any",
        "foot_traffic_importance": "medium",
    },
}


@tool
async def get_location_demographics(address: str) -> dict[str, Any]:
    """
    Get demographic data for a location including population, income, age, and education.

    Use this tool to understand WHO lives near a potential business location.
    This helps assess if the local population matches the target customer profile.

    Args:
        address: The address to analyze (e.g., "123 Main St, Austin, TX")

    Returns:
        Demographic data including:
        - Population statistics
        - Median household income
        - Age distribution
        - Education levels
        - Housing information
    """
    maps_client = get_maps_client()
    census_client = get_census_client()

    # First geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]
    logger.info("Getting demographics for location", lat=lat, lng=lng)

    # Get Census geography for these coordinates
    geo = await census_client.get_geography_for_coordinates(lat, lng)
    if not geo:
        return {
            "error": "Could not determine Census geography for this location",
            "location": location,
        }

    # Get demographic data
    demographics = await census_client.get_demographics(
        state_fips=geo["state_fips"],
        county_fips=geo["county_fips"],
        tract_fips=geo.get("tract_fips"),
    )

    return {
        "location": location,
        "geography": {
            "county": geo.get("county_name", ""),
            "state": geo.get("state_name", ""),
        },
        "demographics": demographics,
    }


@tool
async def analyze_competition_density(
    address: str,
    business_type: str,
    radius_meters: int = 1500,
) -> dict[str, Any]:
    """
    Analyze the competition density for a specific business type at a location.

    Use this tool to understand how saturated the market is with similar businesses.

    Args:
        address: The address to analyze
        business_type: Type of business (e.g., "coffee shop", "gym", "restaurant")
        radius_meters: Search radius in meters (default 1500m)

    Returns:
        Competition analysis including:
        - Number of competitors
        - Average competitor rating
        - Competition density level (low/moderate/high/saturated)
        - Top competitors with details
    """
    maps_client = get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Search for competitors
    competitors = await maps_client.nearby_search(
        lat=lat,
        lng=lng,
        radius=radius_meters,
        keyword=business_type,
    )

    # Analyze competition
    competitor_count = len(competitors)

    # Determine saturation level
    if competitor_count == 0:
        saturation = "none"
        saturation_score = 100  # Great - no competition
    elif competitor_count <= 2:
        saturation = "low"
        saturation_score = 85
    elif competitor_count <= 5:
        saturation = "moderate"
        saturation_score = 65
    elif competitor_count <= 10:
        saturation = "high"
        saturation_score = 40
    else:
        saturation = "saturated"
        saturation_score = 20

    # Calculate average rating
    rated_competitors = [c for c in competitors if c.get("rating")]
    avg_rating = (
        sum(c["rating"] for c in rated_competitors) / len(rated_competitors)
        if rated_competitors
        else 0
    )

    # Get top competitors (highest rated)
    top_competitors = sorted(
        competitors,
        key=lambda x: (x.get("rating", 0), x.get("user_ratings_total", 0)),
        reverse=True,
    )[:5]

    return {
        "location": location,
        "business_type": business_type,
        "radius_meters": radius_meters,
        "competition_analysis": {
            "total_competitors": competitor_count,
            "saturation_level": saturation,
            "saturation_score": saturation_score,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
        },
        "top_competitors": [
            {
                "name": c.get("name"),
                "rating": c.get("rating"),
                "reviews": c.get("user_ratings_total"),
                "address": c.get("vicinity"),
            }
            for c in top_competitors
        ],
    }


@tool
async def assess_foot_traffic_potential(address: str) -> dict[str, Any]:
    """
    Assess the foot traffic potential at a location based on nearby businesses and amenities.

    Use this tool to understand how much pedestrian activity a location might have.
    High foot traffic generally means more potential walk-in customers.

    Args:
        address: The address to analyze

    Returns:
        Foot traffic assessment including:
        - Transit access (nearby stations)
        - Nearby restaurants/cafes (foot traffic generators)
        - Nearby retail (shopping activity)
        - Overall foot traffic score
    """
    maps_client = get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Get various foot traffic indicators in parallel
    transit, restaurants, cafes, retail = await asyncio.gather(
        maps_client.nearby_search(lat, lng, radius=500, place_type="transit_station"),
        maps_client.nearby_search(lat, lng, radius=400, place_type="restaurant"),
        maps_client.nearby_search(lat, lng, radius=400, place_type="cafe"),
        maps_client.nearby_search(lat, lng, radius=400, place_type="store"),
    )

    # Score calculation
    transit_score = min(len(transit) * 15, 30)  # Max 30 points
    food_score = min((len(restaurants) + len(cafes)) * 3, 35)  # Max 35 points
    retail_score = min(len(retail) * 3, 35)  # Max 35 points

    total_score = transit_score + food_score + retail_score

    # Determine foot traffic level
    if total_score >= 80:
        level = "very_high"
    elif total_score >= 60:
        level = "high"
    elif total_score >= 40:
        level = "moderate"
    elif total_score >= 20:
        level = "low"
    else:
        level = "very_low"

    return {
        "location": location,
        "foot_traffic": {
            "score": total_score,
            "level": level,
            "breakdown": {
                "transit_score": transit_score,
                "food_establishment_score": food_score,
                "retail_score": retail_score,
            },
        },
        "nearby_counts": {
            "transit_stations": len(transit),
            "restaurants": len(restaurants),
            "cafes": len(cafes),
            "retail_stores": len(retail),
        },
        "transit_stations": [
            {"name": t.get("name"), "vicinity": t.get("vicinity")} for t in transit[:3]
        ],
    }


@tool
async def calculate_market_viability(
    address: str,
    business_type: str,
    target_customers: str | None = None,
) -> dict[str, Any]:
    """
    Calculate comprehensive market viability score for a business at a location.

    This is the main tool for determining if a location is suitable for a business.
    It combines demographics, competition, and foot traffic into an overall score.

    Args:
        address: The address to analyze
        business_type: Type of business (e.g., "coffee shop", "gym", "restaurant")
        target_customers: Optional description of target customers

    Returns:
        Comprehensive viability analysis including:
        - Overall viability score (1-100)
        - Demographics match score
        - Competition score
        - Foot traffic score
        - Risk factors
        - Opportunities
        - Recommendations
    """
    logger.info("Calculating market viability", address=address, business_type=business_type)

    # Get all data in parallel for better performance
    demo_data, comp_data, traffic_data = await asyncio.gather(
        get_location_demographics.ainvoke({"address": address}),
        analyze_competition_density.ainvoke({"address": address, "business_type": business_type}),
        assess_foot_traffic_potential.ainvoke({"address": address}),
    )

    # Check for errors
    for data, name in [
        (demo_data, "demographics"),
        (comp_data, "competition"),
        (traffic_data, "foot traffic"),
    ]:
        if "error" in data:
            return {"error": f"Error getting {name}: {data['error']}"}

    # Calculate component scores
    demographics = demo_data.get("demographics", {})
    competition = comp_data.get("competition_analysis", {})
    foot_traffic = traffic_data.get("foot_traffic", {})

    # Demographics score (0-100)
    demo_score = _calculate_demographics_score(demographics, business_type)

    # Competition score (already calculated)
    comp_score = competition.get("saturation_score") or 50

    # Foot traffic score
    traffic_score = foot_traffic.get("score") or 50

    # Weighted overall score
    # Demographics: 30%, Competition: 35%, Foot Traffic: 35%
    overall_score = int(demo_score * 0.30 + comp_score * 0.35 + traffic_score * 0.35)

    # Identify risks and opportunities
    risks = []
    opportunities = []

    # Competition risks
    if competition.get("total_competitors", 0) > 10:
        risks.append("High competition density - market may be saturated")
    elif competition.get("total_competitors", 0) == 0:
        opportunities.append("No direct competitors found - potential first-mover advantage")

    # Demographics insights
    income = demographics.get("income", {}).get("median_household", 0)
    if income and income < 40000:
        risks.append("Lower median household income in area")
    elif income and income > 80000:
        opportunities.append("Higher income area - potential for premium pricing")

    # Foot traffic insights
    if foot_traffic.get("level") in ["very_high", "high"]:
        opportunities.append("High foot traffic area - good walk-in potential")
    elif foot_traffic.get("level") in ["very_low", "low"]:
        risks.append("Low foot traffic - may need strong marketing to attract customers")

    # Transit insights
    transit_count = traffic_data.get("nearby_counts", {}).get("transit_stations", 0)
    if transit_count > 0:
        opportunities.append(f"Good transit access ({transit_count} stations nearby)")
    else:
        risks.append("No transit stations nearby - customers will need parking")

    # Generate recommendations
    recommendations = _generate_recommendations(
        overall_score, demo_score, comp_score, traffic_score, risks, opportunities
    )

    return {
        "location": demo_data.get("location"),
        "business_type": business_type,
        "viability_score": overall_score,
        "score_breakdown": {
            "demographics_score": demo_score,
            "competition_score": comp_score,
            "foot_traffic_score": traffic_score,
        },
        "viability_level": _score_to_level(overall_score),
        "demographics_summary": {
            "population": demographics.get("population", {}).get("total"),
            "median_income": demographics.get("income", {}).get("median_household"),
            "median_age": demographics.get("age_distribution", {}).get("median_age"),
            "college_educated_percent": demographics.get("education", {}).get(
                "college_plus_percent"
            ),
        },
        "competition_summary": {
            "competitor_count": competition.get("total_competitors"),
            "saturation_level": competition.get("saturation_level"),
            "average_rating": competition.get("average_rating"),
        },
        "foot_traffic_summary": {
            "level": foot_traffic.get("level"),
            "transit_access": transit_count > 0,
            "nearby_businesses": (
                traffic_data.get("nearby_counts", {}).get("restaurants", 0)
                + traffic_data.get("nearby_counts", {}).get("retail_stores", 0)
            ),
        },
        "risk_factors": risks,
        "opportunities": opportunities,
        "recommendations": recommendations,
        "top_competitors": comp_data.get("top_competitors", []),
    }


def _calculate_demographics_score(demographics: dict, business_type: str) -> int:
    """Calculate demographics match score for a business type."""
    score = 50  # Base score

    income = demographics.get("income", {}).get("median_household", 0)
    age_18_34 = demographics.get("age_distribution", {}).get("age_18_34_percent", 0)
    college = demographics.get("education", {}).get("college_plus_percent", 0)

    # Get ideal demographics for business type
    ideal = BUSINESS_DEMOGRAPHICS.get(
        business_type.lower().replace(" ", "_"),
        BUSINESS_DEMOGRAPHICS.get("retail", {}),  # Default to retail
    )

    # Income scoring
    if income:
        if income > 70000:
            score += 20
        elif income > 50000:
            score += 10
        elif income < 35000:
            score -= 10

    # Age scoring (for businesses targeting younger demographics)
    if ideal.get("ideal_age", "").startswith("18"):
        if age_18_34 and age_18_34 > 30:
            score += 15
        elif age_18_34 and age_18_34 > 20:
            score += 5

    # Education scoring (for businesses targeting educated demographics)
    if ideal.get("ideal_education") == "college_educated":
        if college and college > 40:
            score += 15
        elif college and college > 25:
            score += 5

    return max(0, min(100, score))


def _score_to_level(score: int | None) -> str:
    """Convert numeric score to viability level."""
    if score is None:
        return "unknown"
    if score >= 80:
        return "excellent"
    elif score >= 65:
        return "good"
    elif score >= 50:
        return "moderate"
    elif score >= 35:
        return "challenging"
    else:
        return "poor"


def _generate_recommendations(
    overall: int | None,
    demo: int | None,
    comp: int | None,
    traffic: int | None,
    risks: list,
    opportunities: list,
) -> list[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations = []

    if overall is None:
        recommendations.append("Unable to calculate overall viability - some data may be missing")
    elif overall >= 70:
        recommendations.append("This location shows strong potential for your business")
    elif overall >= 50:
        recommendations.append(
            "This location has moderate potential - consider the specific risks identified"
        )
    else:
        recommendations.append("This location may be challenging - carefully evaluate alternatives")

    # Specific recommendations based on scores
    if comp is not None and comp < 50:
        recommendations.append(
            "Consider differentiation strategies to stand out from existing competitors"
        )

    if traffic is not None and traffic < 50:
        recommendations.append(
            "Plan for strong marketing and signage to attract customers to this location"
        )

    if demo is not None and demo < 50:
        recommendations.append(
            "The local demographics may not perfectly match your target market - consider marketing strategies to reach customers from surrounding areas"
        )

    if len(opportunities) > len(risks):
        recommendations.append(
            "The opportunities outweigh the risks - this could be a good choice with proper planning"
        )

    return recommendations


# List of all tools for the agent
MARKET_VALIDATOR_TOOLS = [
    get_location_demographics,
    analyze_competition_density,
    assess_foot_traffic_potential,
    calculate_market_viability,
]
