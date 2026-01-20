"""LangChain tools for economic intelligence and trend analysis."""

from typing import Any, TYPE_CHECKING
from langchain_core.tools import tool

# Use lazy imports to avoid circular dependencies
if TYPE_CHECKING:
    from ...services.economic_service import EconomicService
    from ...services.market_analysis_service import MarketAnalysisService


def _get_economic_service():
    """Lazy import for economic service."""
    from ...services.economic_service import get_economic_service
    return get_economic_service()


def _get_market_analysis_service():
    """Lazy import for market analysis service."""
    from ...services.market_analysis_service import get_market_analysis_service
    return get_market_analysis_service()


def _get_naics_service():
    """Lazy import for NAICS service."""
    from .naics_service import get_naics_service
    return get_naics_service()


@tool
async def get_economic_indicators(region: str | None = None) -> dict[str, Any]:
    """
    Get current economic indicators and outlook for business planning.

    Use this tool when:
    - User asks about economic conditions
    - User wants to know if it's a good time to start a business
    - User asks about unemployment, consumer confidence, or inflation
    - User wants economic context for their market analysis

    Args:
        region: Optional state code (e.g., "TX", "CA") for regional data.
               Leave empty for national data.

    Returns:
        Economic snapshot with key indicators, interpretations, and outlook.

    Example:
        get_economic_indicators()  # National data
        get_economic_indicators("WA")  # Washington state data
    """
    service = _get_economic_service()
    return await service.get_economic_snapshot(region)


@tool
async def analyze_industry_trends(
    naics_code: str | None = None,
    business_type: str | None = None,
) -> dict[str, Any]:
    """
    Analyze industry trends from employment data and news coverage.

    Use this tool when:
    - User asks about industry trends or outlook
    - User wants to know if an industry is growing or declining
    - User asks "Is X industry doing well?"
    - User wants trend data for business planning

    Args:
        naics_code: NAICS industry code (e.g., "722515" for coffee shops)
        business_type: Business type description (used if naics_code not provided)

    Returns:
        Trend analysis with direction, growth rate, signals, and recommendations.

    Example:
        analyze_industry_trends(naics_code="722515")
        analyze_industry_trends(business_type="fitness center")
    """
    market_service = _get_market_analysis_service()
    naics_service = _get_naics_service()

    # Resolve NAICS code
    if not naics_code and business_type:
        codes = naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "722515"
    elif not naics_code:
        return {"error": "Either naics_code or business_type must be provided"}

    return await market_service.analyze_industry_trends(naics_code)


@tool
async def get_seasonality_pattern(
    naics_code: str | None = None,
    business_type: str | None = None,
) -> dict[str, Any]:
    """
    Get seasonal business patterns for an industry.

    Use this tool when:
    - User asks about peak seasons or slow periods
    - User wants to understand seasonal patterns
    - User asks "When is the best time to open X?"
    - User needs to plan for seasonal variations

    Args:
        naics_code: NAICS industry code
        business_type: Business type (used if naics_code not provided)

    Returns:
        Monthly seasonality indices with peak/low months and recommendations.

    Example:
        get_seasonality_pattern(business_type="gym")
    """
    service = _get_economic_service()
    naics_service = _get_naics_service()

    # Resolve NAICS code
    if not naics_code and business_type:
        codes = naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "722515"
    elif not naics_code:
        return {"error": "Either naics_code or business_type must be provided"}

    return service.get_seasonality_pattern(naics_code)


@tool
async def analyze_entry_timing(
    business_type: str,
    state: str | None = None,
) -> dict[str, Any]:
    """
    Analyze optimal timing for market entry combining economic and seasonal factors.

    Use this tool when:
    - User asks when to start their business
    - User wants timing recommendations
    - User asks "Is now a good time to open X?"
    - User needs comprehensive timing analysis

    This combines economic conditions, industry trends, and seasonality to provide
    timing recommendations.

    Args:
        business_type: Type of business (e.g., "coffee shop", "gym")
        state: Optional state code for regional economic data

    Returns:
        Timing analysis with optimal months, economic context, and recommendations.

    Example:
        analyze_entry_timing("coffee shop", "CA")
    """
    service = _get_economic_service()
    location = {"state": state} if state else None
    return await service.analyze_entry_timing(business_type, location)


@tool
async def get_consumer_spending_trends(category: str | None = None) -> dict[str, Any]:
    """
    Get consumer spending trends to understand market conditions.

    Use this tool when:
    - User asks about consumer spending
    - User wants to understand spending patterns
    - User asks "Are people spending money on X?"

    Args:
        category: Optional spending category (currently returns overall retail)

    Returns:
        Spending trend data with direction and interpretation.

    Example:
        get_consumer_spending_trends()
    """
    service = _get_economic_service()
    return await service.get_consumer_spending_trends(category)


@tool
async def get_economic_summary(
    business_type: str,
    state: str | None = None,
) -> dict[str, Any]:
    """
    Get comprehensive economic and timing summary for business planning.

    Use this tool for a complete economic analysis that combines:
    - Economic indicators and outlook
    - Industry trends
    - Seasonality patterns
    - Entry timing recommendations

    Args:
        business_type: Type of business
        state: Optional state code for regional data

    Returns:
        Comprehensive economic summary for business planning.

    Example:
        get_economic_summary("restaurant", "TX")
    """
    economic_service = _get_economic_service()
    market_service = _get_market_analysis_service()
    naics_service = _get_naics_service()

    # Get NAICS code
    codes = naics_service.map_business_type(business_type)
    naics_code = codes[0] if codes else "722515"

    # Gather all economic data
    location = {"state": state} if state else None

    economic_snapshot = await economic_service.get_economic_snapshot(state)
    industry_trends = await market_service.analyze_industry_trends(naics_code)
    seasonality = economic_service.get_seasonality_pattern(naics_code)
    entry_timing = await economic_service.analyze_entry_timing(business_type, location)

    return {
        "summary": {
            "business_type": business_type,
            "region": state or "national",
            "naics_code": naics_code,
        },
        "economic_conditions": {
            "outlook": economic_snapshot.get("outlook", {}),
            "key_indicators": {
                k: v.get("value")
                for k, v in economic_snapshot.get("indicators", {}).items()
                if isinstance(v, dict)
            },
        },
        "industry_trends": {
            "direction": industry_trends.get("trend_direction"),
            "growth_rate": industry_trends.get("employment_growth_rate"),
            "signals": industry_trends.get("signals", []),
        },
        "seasonality": {
            "peak_month": seasonality.get("peak_month"),
            "low_month": seasonality.get("low_month"),
            "variability": seasonality.get("variability"),
        },
        "timing": {
            "score": entry_timing.get("timing_score"),
            "optimal_months": entry_timing.get("optimal_months"),
            "recommendation": entry_timing.get("recommendation"),
        },
        "key_insights": _generate_economic_insights(
            economic_snapshot, industry_trends, entry_timing
        ),
    }


def _generate_economic_insights(
    economic: dict, trends: dict, timing: dict
) -> list[str]:
    """Generate key insights from economic data."""
    insights = []

    # Economic outlook insight
    outlook = economic.get("outlook", {}).get("level", "neutral")
    if outlook == "favorable":
        insights.append("Economic conditions are favorable for new businesses")
    elif outlook == "challenging":
        insights.append("Economic headwinds present - plan conservatively")

    # Industry trend insight
    direction = trends.get("trend_direction", "stable")
    if direction in ["growing", "strongly_growing"]:
        insights.append(f"Industry is {direction.replace('_', ' ')} - positive momentum")
    elif direction == "declining":
        insights.append("Industry facing challenges - differentiation critical")

    # Timing insight
    timing_score = timing.get("timing_score", 50)
    if timing_score >= 75:
        insights.append("Current timing is favorable for market entry")
    elif timing_score <= 40:
        insights.append("Consider waiting for better conditions")

    return insights if insights else ["Market conditions are neutral - standard planning applies"]


# List of all economic intelligence tools
ECONOMIC_TOOLS = [
    get_economic_indicators,
    analyze_industry_trends,
    get_seasonality_pattern,
    analyze_entry_timing,
    get_consumer_spending_trends,
    get_economic_summary,
]
