"""LangChain tools for financial projections and scenario analysis."""

from typing import Any
from langchain_core.tools import tool


def _get_financial_service():
    """Lazy import for financial analysis service."""
    from ...services.financial_analysis_service import get_financial_analysis_service
    return get_financial_analysis_service()


def _get_maps_client():
    """Lazy import for Google Maps client."""
    from ..location_scout.google_maps import GoogleMapsClient
    return GoogleMapsClient()


async def _gather_market_data(address: str, business_type: str, location: dict) -> dict:
    """Gather market data for financial analysis."""
    market_data = {
        "demographics": {},
        "competitors": [],
        "som": {},
        "trends": {},
        "economic": {},
    }

    # Try to get demographics
    try:
        from ..market_validator.census_client import CensusClient
        census = CensusClient()
        demographics = await census.get_demographics(location["lat"], location["lng"])
        if demographics:
            market_data["demographics"] = demographics
    except Exception:
        market_data["demographics"] = {"total_population": 50000, "median_income": 60000}

    # Try to get competitors
    try:
        from ..competitor_analyzer.agent_tools import find_competitors
        result = await find_competitors.ainvoke({
            "address": address,
            "business_type": business_type,
            "radius_meters": 1500,
        })
        if "competitors" in result:
            market_data["competitors"] = result["competitors"]
    except Exception:
        pass

    # Try to get market size
    try:
        from ...services.market_analysis_service import get_market_analysis_service
        market_service = get_market_analysis_service()
        size = await market_service.calculate_market_size(
            location, business_type, radius_miles=1.5
        )
        market_data["som"] = size.get("som", {})
    except Exception:
        pass

    # Try to get trends
    try:
        from ...services.market_analysis_service import get_market_analysis_service
        from .naics_service import get_naics_service
        naics = get_naics_service()
        codes = naics.map_business_type(business_type)
        if codes:
            market_service = get_market_analysis_service()
            trends = await market_service.analyze_industry_trends(codes[0])
            market_data["trends"] = trends
    except Exception:
        pass

    return market_data


@tool
async def project_revenue(
    address: str,
    business_type: str,
    scenario: str = "moderate",
) -> dict[str, Any]:
    """
    Project revenue for a business at a specific location.

    Use this tool when:
    - User asks about revenue potential
    - User wants revenue projections or estimates
    - User asks "How much can I make?"
    - User wants financial projections

    Projects daily, monthly, and annual revenue based on industry benchmarks
    and local market factors.

    Args:
        address: The address for the business
        business_type: Type of business
        scenario: "conservative", "moderate", or "optimistic"

    Returns:
        Revenue projection with assumptions and benchmark comparison.

    Example:
        project_revenue("Austin, TX", "coffee shop", "moderate")
    """
    service = _get_financial_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data
    market_data = await _gather_market_data(address, business_type, location)

    result = service.project_revenue(business_type, location, market_data, scenario)
    result["location"] = address

    return result


@tool
async def calculate_break_even(
    address: str,
    business_type: str,
    monthly_fixed_costs: float | None = None,
) -> dict[str, Any]:
    """
    Calculate break-even point and startup recovery timeline.

    Use this tool when:
    - User asks about break-even
    - User wants to know when they'll be profitable
    - User asks "How long until I make money?"
    - User wants break-even analysis

    Calculates break-even revenue, units needed, and months to recover
    startup investment.

    Args:
        address: The address for the business
        business_type: Type of business
        monthly_fixed_costs: Optional monthly fixed costs (uses benchmark if not provided)

    Returns:
        Break-even analysis with timeline and benchmark comparison.

    Example:
        calculate_break_even("Seattle, WA", "restaurant")
    """
    service = _get_financial_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Get revenue projection for context
    market_data = await _gather_market_data(address, business_type, location)
    revenue_projection = service.project_revenue(business_type, location, market_data, "moderate")

    result = service.calculate_break_even(
        business_type,
        revenue_projection,
        fixed_costs=monthly_fixed_costs,
    )
    result["location"] = address

    return result


@tool
async def run_financial_scenario(
    address: str,
    business_type: str,
    price_change_percent: float = 0,
    cost_reduction_percent: float = 0,
    volume_change_percent: float = 0,
) -> dict[str, Any]:
    """
    Run what-if financial scenario analysis.

    Use this tool when:
    - User wants to explore "what if" scenarios
    - User asks about impact of price changes
    - User asks "What if I reduce costs?"
    - User wants scenario modeling

    Analyzes impact of changes to pricing, costs, or volume on
    revenue and profitability.

    Args:
        address: The address for the business
        business_type: Type of business
        price_change_percent: Percent change in prices (e.g., 10 for 10% increase)
        cost_reduction_percent: Percent reduction in costs
        volume_change_percent: Percent change in transaction volume

    Returns:
        Scenario comparison showing impact on revenue and profit.

    Example:
        run_financial_scenario("Portland, OR", "bakery", price_change_percent=5, cost_reduction_percent=10)
    """
    service = _get_financial_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Get base analysis
    market_data = await _gather_market_data(address, business_type, location)
    base_analysis = service.project_revenue(business_type, location, market_data, "moderate")

    # Add profit margin from benchmark
    benchmark = service.get_industry_benchmark(base_analysis.get("naics_code", "default"))
    base_analysis["profit_margin"] = benchmark.get("profit_margin", {}).get("median", 10)

    # Build modifications
    modifications = {
        "name": "Custom Scenario",
        "price_change": price_change_percent,
        "cost_reduction": cost_reduction_percent,
        "volume_change": volume_change_percent,
    }

    result = service.run_scenario(base_analysis, modifications)
    result["location"] = address
    result["business_type"] = business_type

    return result


@tool
async def assess_financial_viability(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Assess overall financial viability of a business.

    Use this tool when:
    - User asks if a business is financially viable
    - User wants viability assessment
    - User asks "Is this a good investment?"
    - User wants overall financial evaluation

    Calculates a viability score (0-100) based on revenue potential,
    margins, break-even timeline, and market factors.

    Args:
        address: The address for the business
        business_type: Type of business

    Returns:
        Viability assessment with score, risk factors, and recommendations.

    Example:
        assess_financial_viability("Brooklyn, NY", "yoga studio")
    """
    service = _get_financial_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data
    market_data = await _gather_market_data(address, business_type, location)

    # Get revenue projection
    revenue_projection = service.project_revenue(business_type, location, market_data, "moderate")

    result = service.calculate_financial_viability(business_type, revenue_projection, market_data)
    result["location"] = address

    return result


@tool
async def get_financial_summary(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Get comprehensive financial summary combining projections, break-even,
    and viability analysis.

    Use this tool for a complete financial analysis that includes:
    - Revenue projections (conservative, moderate, optimistic)
    - Break-even analysis
    - Financial viability score
    - Industry benchmarks
    - Key insights and recommendations

    Args:
        address: The address for the business
        business_type: Type of business

    Returns:
        Comprehensive financial summary.

    Example:
        get_financial_summary("San Francisco, CA", "fitness center")
    """
    service = _get_financial_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather market data
    market_data = await _gather_market_data(address, business_type, location)

    return service.get_financial_summary(business_type, location, market_data)


@tool
def get_industry_benchmarks(
    business_type: str,
) -> dict[str, Any]:
    """
    Get industry financial benchmarks for a business type.

    Use this tool when:
    - User asks about industry averages
    - User wants benchmark data
    - User asks "What's typical for this industry?"
    - User wants cost structure information

    Returns industry benchmarks including average revenue, cost structure,
    profit margins, and startup costs.

    Args:
        business_type: Type of business

    Returns:
        Industry benchmark data.

    Example:
        get_industry_benchmarks("restaurant")
    """
    service = _get_financial_service()

    # Get NAICS code
    codes = service.naics_service.map_business_type(business_type)
    naics_code = codes[0] if codes else "default"

    benchmark = service.get_industry_benchmark(naics_code)

    return {
        "business_type": business_type,
        "naics_code": naics_code,
        "industry_name": benchmark.get("name", business_type),
        "revenue": {
            "average": benchmark.get("avg_revenue_per_location"),
            "range": benchmark.get("revenue_range"),
        },
        "cost_structure": benchmark.get("cost_structure"),
        "profit_margins": benchmark.get("profit_margin"),
        "typical_metrics": {
            "avg_ticket": benchmark.get("avg_ticket"),
            "transactions_per_day": benchmark.get("transactions_per_day"),
        },
        "startup": {
            "costs": benchmark.get("startup_costs"),
            "break_even_months": benchmark.get("break_even_months"),
        },
    }


# List of all financial tools
FINANCIAL_TOOLS = [
    project_revenue,
    calculate_break_even,
    run_financial_scenario,
    assess_financial_viability,
    get_financial_summary,
    get_industry_benchmarks,
]
