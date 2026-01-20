"""LangChain tools for market sizing and TAM/SAM/SOM analysis."""

from typing import Any, TYPE_CHECKING
from langchain_core.tools import tool

# Use lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from ...services.market_analysis_service import MarketAnalysisService


def _get_market_analysis_service():
    """Lazy import to avoid circular dependency."""
    from ...services.market_analysis_service import get_market_analysis_service
    return get_market_analysis_service()


def _get_naics_service():
    """Lazy import for NAICS service."""
    from .naics_service import get_naics_service
    return get_naics_service()


@tool
async def calculate_market_size(
    address: str,
    business_type: str,
    radius_miles: float = 5.0,
    competitor_count: int | None = None,
) -> dict[str, Any]:
    """
    Calculate Total Addressable Market (TAM), Serviceable Available Market (SAM),
    and Serviceable Obtainable Market (SOM) for a business location.

    Use this tool when:
    - User asks about market size or market opportunity
    - User wants to know potential revenue for an area
    - User asks "How big is the market for X in Y?"
    - User wants TAM/SAM/SOM analysis

    This is the primary tool for understanding market opportunity and potential.

    Args:
        address: The business address or location (e.g., "Capitol Hill, Seattle, WA")
        business_type: Type of business (e.g., "coffee shop", "gym", "restaurant")
        radius_miles: Service radius in miles (default 5.0)
        competitor_count: Known number of competitors (improves SOM accuracy)

    Returns:
        Market size breakdown with TAM (theoretical maximum), SAM (realistic target),
        and SOM (achievable first-year capture), plus methodology explanation.

    Example:
        calculate_market_size("Downtown Austin, TX", "coffee shop", 3.0, 15)
    """
    service = _get_market_analysis_service()

    # Create location dict - will be geocoded by service
    location = {"address": address}

    result = await service.calculate_market_size(
        location=location,
        business_type=business_type,
        radius_miles=radius_miles,
        competitor_count=competitor_count,
    )

    return result


@tool
async def get_industry_profile(naics_code: str | None = None, business_type: str | None = None) -> dict[str, Any]:
    """
    Get comprehensive industry profile including size, growth trends, and economic context.

    Use this tool when:
    - User asks about an industry's performance or outlook
    - User wants to understand industry trends
    - User asks "How is the X industry doing?"
    - User wants employment and wage data for an industry

    Args:
        naics_code: NAICS industry code (e.g., "722515" for coffee shops).
                   If not provided, business_type must be specified.
        business_type: Business type description (e.g., "coffee shop").
                      Used to look up NAICS code if not provided.

    Returns:
        Industry profile with employment data, growth trends, economic context,
        and industry hierarchy.

    Example:
        get_industry_profile(naics_code="722515")
        get_industry_profile(business_type="fitness center")
    """
    service = _get_market_analysis_service()
    naics_service = _get_naics_service()

    # Resolve NAICS code if not provided
    if not naics_code and business_type:
        codes = naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "722515"
    elif not naics_code:
        return {"error": "Either naics_code or business_type must be provided"}

    return await service.get_industry_profile(naics_code)


@tool
async def analyze_labor_market(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Analyze labor market conditions for hiring staff at a location.

    Use this tool when:
    - User asks about hiring difficulty or labor availability
    - User wants to know typical wages for the area/industry
    - User asks "Can I find employees for X in Y?"
    - User asks about workforce availability

    Args:
        address: Business location address
        business_type: Type of business (determines occupation analysis)

    Returns:
        Labor market analysis including workforce size, wage data,
        hiring difficulty score, and recommendations.

    Example:
        analyze_labor_market("Seattle, WA", "restaurant")
    """
    service = _get_market_analysis_service()

    # Create location dict
    location = {"address": address}

    return await service.analyze_labor_market(
        location=location,
        business_type=business_type,
    )


@tool
async def project_market_growth(
    current_market_size: float,
    naics_code: str | None = None,
    business_type: str | None = None,
    years: int = 5,
) -> dict[str, Any]:
    """
    Project market size growth over time based on industry trends.

    Use this tool when:
    - User asks about future market potential
    - User wants market projections for planning
    - User asks "What will the market be worth in X years?"

    Args:
        current_market_size: Current TAM or market size in dollars
        naics_code: NAICS code for industry growth rate lookup
        business_type: Business type (used if naics_code not provided)
        years: Number of years to project (default 5)

    Returns:
        Projected market sizes for each year with growth rate details.

    Example:
        project_market_growth(5000000, business_type="coffee shop", years=5)
    """
    service = _get_market_analysis_service()
    naics_service = _get_naics_service()

    # Resolve NAICS code
    if not naics_code and business_type:
        codes = naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "722515"
    elif not naics_code:
        naics_code = "722515"

    # Get growth rate
    growth_data = await service.calculate_growth_rate(naics_code)
    growth_rate = growth_data.get("blended_growth_rate", 2.5)

    # Project market size
    projections = await service.project_market_size(
        current_tam=current_market_size,
        growth_rate=growth_rate,
        years=years,
    )

    return {
        "current_market_size": current_market_size,
        "growth_rate_percent": growth_rate,
        "growth_rate_source": growth_data.get("source"),
        **projections,
    }


@tool
async def get_market_sizing_summary(
    address: str,
    business_type: str,
    radius_miles: float = 5.0,
) -> dict[str, Any]:
    """
    Get a comprehensive market sizing summary combining TAM/SAM/SOM with
    industry profile and growth projections.

    Use this tool for a complete market opportunity overview. This combines
    multiple analyses into one comprehensive result.

    Use this when:
    - User wants a full market analysis
    - User asks "Should I open X in Y?" (market perspective)
    - User wants the complete market picture

    Args:
        address: Business location address
        business_type: Type of business
        radius_miles: Service radius in miles

    Returns:
        Comprehensive market summary with size, growth, industry profile,
        and key recommendations.

    Example:
        get_market_sizing_summary("Portland, OR", "yoga studio", 3.0)
    """
    service = _get_market_analysis_service()
    naics_service = _get_naics_service()

    # Get NAICS code
    codes = naics_service.map_business_type(business_type)
    naics_code = codes[0] if codes else "722515"

    # Run multiple analyses
    location = {"address": address}

    market_size = await service.calculate_market_size(
        location=location,
        business_type=business_type,
        radius_miles=radius_miles,
    )

    industry_profile = await service.get_industry_profile(naics_code)
    growth_data = await service.calculate_growth_rate(naics_code)

    # Project 5-year growth
    tam = market_size["tam"]["value"]
    projections = await service.project_market_size(
        current_tam=tam,
        growth_rate=growth_data.get("blended_growth_rate", 2.5),
        years=5,
    )

    return {
        "summary": {
            "location": address,
            "business_type": business_type,
            "naics_code": naics_code,
            "industry_name": industry_profile.get("industry_name"),
        },
        "market_size": market_size,
        "industry_profile": {
            "employment_trend": industry_profile.get("employment", {}).get("trend"),
            "growth_rate": industry_profile.get("employment", {}).get("growth_rate"),
            "economic_context": industry_profile.get("economic_context"),
        },
        "growth_projections": projections,
        "key_insights": _generate_market_insights(market_size, industry_profile, growth_data),
    }


def _generate_market_insights(
    market_size: dict, industry_profile: dict, growth_data: dict
) -> list[str]:
    """Generate key insights from market data."""
    insights = []

    # Market size insights
    tam = market_size.get("tam", {}).get("value", 0)
    som = market_size.get("som", {}).get("value", 0)

    if tam > 10_000_000:
        insights.append("Large addressable market (>$10M TAM)")
    elif tam > 5_000_000:
        insights.append("Moderate addressable market ($5-10M TAM)")
    else:
        insights.append("Smaller addressable market (<$5M TAM)")

    # Growth insights
    growth = growth_data.get("blended_growth_rate", 0)
    if growth > 4:
        insights.append(f"Strong industry growth ({growth:.1f}% annually)")
    elif growth > 2:
        insights.append(f"Moderate industry growth ({growth:.1f}% annually)")
    elif growth > 0:
        insights.append(f"Slow industry growth ({growth:.1f}% annually)")
    else:
        insights.append("Industry showing decline - consider positioning carefully")

    # Employment trend insights
    trend = industry_profile.get("employment", {}).get("trend")
    if trend == "growing":
        insights.append("Industry employment is growing - positive market signal")
    elif trend == "declining":
        insights.append("Industry employment declining - potential market headwinds")

    # Confidence note
    confidence = market_size.get("confidence", {}).get("level", "medium")
    insights.append(f"Analysis confidence: {confidence}")

    return insights


# List of all market sizing tools
MARKET_SIZING_TOOLS = [
    calculate_market_size,
    get_industry_profile,
    analyze_labor_market,
    project_market_growth,
    get_market_sizing_summary,
]
