"""LangChain tools for advanced competitive intelligence and strategic analysis."""

from typing import Any
from langchain_core.tools import tool


def _get_competitive_analysis_service():
    """Lazy import for competitive analysis service."""
    from ...services.competitive_analysis_service import get_competitive_analysis_service
    return get_competitive_analysis_service()


def _get_maps_client():
    """Lazy import for Google Maps client."""
    from ..location_scout.google_maps import GoogleMapsClient
    return GoogleMapsClient()


def _get_competitor_tools():
    """Lazy import for competitor finder function."""
    from ..competitor_analyzer.agent_tools import find_competitors
    return find_competitors


@tool
async def generate_swot_analysis(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Generate a SWOT analysis for a business at a specific location.

    Use this tool when:
    - User asks for SWOT analysis
    - User wants to understand strengths, weaknesses, opportunities, threats
    - User asks "What are the pros and cons of opening X here?"
    - User needs strategic market assessment

    This tool gathers market data and generates a comprehensive SWOT analysis
    with data-backed insights for each quadrant.

    Args:
        address: The address/location for the business
        business_type: Type of business (e.g., "coffee shop", "gym")

    Returns:
        SWOT analysis with strengths, weaknesses, opportunities, threats,
        and an overall assessment score with recommendations.

    Example:
        generate_swot_analysis("123 Main St, Seattle, WA", "yoga studio")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data for SWOT analysis
    market_data = await _gather_market_data(address, business_type, location)

    return await service.generate_swot(location, business_type, market_data)


@tool
async def analyze_competitive_forces(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Analyze Porter's Five Forces for a business market.

    Use this tool when:
    - User asks about competitive forces or industry structure
    - User wants Porter's Five Forces analysis
    - User asks "How competitive is the X industry?"
    - User asks about barriers to entry or supplier/buyer power

    This analyzes the five competitive forces that shape industry competition:
    1. Competitive Rivalry
    2. Supplier Power
    3. Buyer Power
    4. Threat of Substitutes
    5. Threat of New Entrants

    Args:
        address: The address/location for analysis
        business_type: Type of business

    Returns:
        Five Forces analysis with scores, rationale, and overall industry attractiveness.

    Example:
        analyze_competitive_forces("Downtown Portland, OR", "fitness center")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data
    market_data = await _gather_market_data(address, business_type, location)

    return await service.analyze_five_forces(business_type, location, market_data)


@tool
async def estimate_market_shares(
    address: str,
    business_type: str,
    radius_meters: int = 1500,
) -> dict[str, Any]:
    """
    Estimate market share distribution among competitors.

    Use this tool when:
    - User asks about market share
    - User wants to know who dominates the market
    - User asks "Who are the biggest players?"
    - User asks about market concentration

    Uses review counts, ratings, and pricing as proxies to estimate relative
    market share among competitors.

    Args:
        address: The address to search around
        business_type: Type of business
        radius_meters: Search radius (default 1500m)

    Returns:
        Market share estimates with leader identification and concentration analysis.

    Example:
        estimate_market_shares("Capitol Hill, Seattle", "coffee shop")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode and find competitors
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    # Get competitors using existing tool
    find_competitors_tool = _get_competitor_tools()
    competitor_result = await find_competitors_tool.ainvoke({
        "address": address,
        "business_type": business_type,
        "radius_meters": radius_meters,
    })

    if "error" in competitor_result:
        return competitor_result

    competitors = competitor_result.get("competitors", [])

    result = service.estimate_market_shares(competitors)
    result["location"] = address
    result["business_type"] = business_type
    result["radius_meters"] = radius_meters

    return result


@tool
async def analyze_pricing_landscape(
    address: str,
    business_type: str,
    radius_meters: int = 1500,
) -> dict[str, Any]:
    """
    Analyze competitor pricing strategies and identify gaps.

    Use this tool when:
    - User asks about pricing in the market
    - User wants to understand price positioning
    - User asks "What do competitors charge?"
    - User asks about pricing strategy or gaps

    Analyzes the distribution of competitor pricing tiers and identifies
    potential pricing opportunities.

    Args:
        address: The address to search around
        business_type: Type of business
        radius_meters: Search radius (default 1500m)

    Returns:
        Pricing analysis with distribution, gaps, and recommendations.

    Example:
        analyze_pricing_landscape("SoMa, San Francisco", "restaurant")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode and find competitors
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    # Get competitors
    find_competitors_tool = _get_competitor_tools()
    competitor_result = await find_competitors_tool.ainvoke({
        "address": address,
        "business_type": business_type,
        "radius_meters": radius_meters,
    })

    if "error" in competitor_result:
        return competitor_result

    competitors = competitor_result.get("competitors", [])

    result = service.analyze_pricing_landscape(competitors)
    result["location"] = address
    result["business_type"] = business_type

    return result


@tool
async def benchmark_competitors(
    address: str,
    business_type: str,
    planned_price_level: int = 2,
    target_quality: str = "high",
) -> dict[str, Any]:
    """
    Benchmark your planned business against existing competitors.

    Use this tool when:
    - User wants to compare their business plan to competitors
    - User asks "How does my business compare?"
    - User asks about competitive advantages/gaps
    - User wants benchmarking analysis

    Compares a planned business profile against market benchmarks to identify
    competitive advantages and gaps.

    Args:
        address: The address for the planned business
        business_type: Type of business
        planned_price_level: Planned price tier (1=budget, 2=value, 3=premium, 4=luxury)
        target_quality: Target quality level ("low", "medium", "high")

    Returns:
        Benchmarking analysis with advantages, gaps, and recommendations.

    Example:
        benchmark_competitors("Austin, TX", "pizza restaurant", 2, "high")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode and find competitors
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    # Get competitors
    find_competitors_tool = _get_competitor_tools()
    competitor_result = await find_competitors_tool.ainvoke({
        "address": address,
        "business_type": business_type,
        "radius_meters": 1500,
    })

    if "error" in competitor_result:
        return competitor_result

    competitors = competitor_result.get("competitors", [])

    business_profile = {
        "price_level": planned_price_level,
        "target_quality": target_quality,
        "business_type": business_type,
    }

    result = service.benchmark_against_competitors(business_profile, competitors)
    result["location"] = address

    return result


@tool
async def get_competitive_intelligence_summary(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Get comprehensive competitive intelligence combining SWOT, Five Forces,
    market share, and pricing analysis.

    Use this tool for a complete competitive analysis that includes:
    - SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats)
    - Porter's Five Forces assessment
    - Market share distribution
    - Pricing landscape analysis
    - Strategic recommendations

    Args:
        address: The address/location for analysis
        business_type: Type of business

    Returns:
        Comprehensive competitive intelligence summary.

    Example:
        get_competitive_intelligence_summary("Brooklyn, NY", "bakery")
    """
    service = _get_competitive_analysis_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data
    market_data = await _gather_market_data(address, business_type, location)
    competitors = market_data.get("competitors", [])

    # Run all analyses
    swot = await service.generate_swot(location, business_type, market_data)
    five_forces = await service.analyze_five_forces(business_type, location, market_data)
    market_shares = service.estimate_market_shares(competitors)
    pricing = service.analyze_pricing_landscape(competitors)

    # Generate key insights
    insights = _generate_competitive_insights(swot, five_forces, market_shares, pricing)

    return {
        "location": address,
        "business_type": business_type,
        "competitor_count": len(competitors),
        "swot_summary": {
            "assessment": swot.get("assessment", {}),
            "top_strength": swot.get("strengths", [{}])[0] if swot.get("strengths") else None,
            "top_opportunity": swot.get("opportunities", [{}])[0] if swot.get("opportunities") else None,
            "top_threat": swot.get("threats", [{}])[0] if swot.get("threats") else None,
        },
        "five_forces_summary": five_forces.get("overall", {}),
        "market_concentration": market_shares.get("concentration", {}),
        "pricing_summary": {
            "dominant_tier": pricing.get("dominant_tier"),
            "gaps": pricing.get("pricing_gaps", []),
        },
        "key_insights": insights,
        "full_swot": swot,
        "full_five_forces": five_forces,
    }


async def _gather_market_data(address: str, business_type: str, location: dict) -> dict:
    """Gather market data from various sources for analysis."""
    # Get competitors
    find_competitors_tool = _get_competitor_tools()
    competitor_result = await find_competitors_tool.ainvoke({
        "address": address,
        "business_type": business_type,
        "radius_meters": 1500,
    })

    competitors = competitor_result.get("competitors", []) if "error" not in competitor_result else []

    # Try to get additional market data (with graceful degradation)
    market_data = {
        "competitors": competitors,
        "demographics": {},
        "economic": {},
        "trends": {},
        "positioning": competitor_result if "error" not in competitor_result else {},
    }

    # Try to get demographics
    try:
        from ..market_validator.census_client import CensusClient
        census = CensusClient()
        demographics = await census.get_demographics(location["lat"], location["lng"])
        if demographics:
            market_data["demographics"] = demographics
    except Exception:
        pass

    # Try to get economic data
    try:
        from ...services.economic_service import get_economic_service
        economic_service = get_economic_service()
        economic = await economic_service.get_economic_snapshot()
        market_data["economic"] = economic
    except Exception:
        pass

    # Try to get industry trends
    try:
        from ...services.market_analysis_service import get_market_analysis_service
        from .naics_service import get_naics_service
        naics_service = get_naics_service()
        market_service = get_market_analysis_service()
        codes = naics_service.map_business_type(business_type)
        if codes:
            trends = await market_service.analyze_industry_trends(codes[0])
            market_data["trends"] = trends
    except Exception:
        pass

    return market_data


def _generate_competitive_insights(
    swot: dict,
    five_forces: dict,
    market_shares: dict,
    pricing: dict,
) -> list[str]:
    """Generate key insights from competitive analysis."""
    insights = []

    # SWOT-based insights
    assessment = swot.get("assessment", {})
    if assessment.get("level") == "favorable":
        insights.append("Market conditions are favorable - strong position for entry")
    elif assessment.get("level") == "challenging":
        insights.append("Significant challenges present - requires differentiation strategy")

    # Five Forces insight
    attractiveness = five_forces.get("overall", {}).get("attractiveness_score", 50)
    if attractiveness >= 65:
        insights.append("Industry structure is attractive for new entrants")
    elif attractiveness < 40:
        insights.append("High competitive forces require careful positioning")

    # Market concentration insight
    concentration = market_shares.get("concentration", {})
    if concentration.get("level") == "fragmented":
        insights.append("Fragmented market offers opportunity to consolidate share")
    elif concentration.get("level") == "concentrated":
        leader = market_shares.get("market_leader", {})
        if leader:
            insights.append(f"Market led by {leader.get('name', 'dominant player')} - niche positioning recommended")

    # Pricing insight
    gaps = pricing.get("pricing_gaps", [])
    if gaps:
        insights.append(f"Pricing opportunity: {gaps[0]}")

    return insights if insights else ["Standard competitive conditions - differentiation through quality recommended"]


# List of all competitive intelligence tools
COMPETITIVE_INTELLIGENCE_TOOLS = [
    generate_swot_analysis,
    analyze_competitive_forces,
    estimate_market_shares,
    analyze_pricing_landscape,
    benchmark_competitors,
    get_competitive_intelligence_summary,
]
