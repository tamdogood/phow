"""LangChain tools for report generation and recommendations."""

from typing import Any
from langchain_core.tools import tool


def _get_report_service():
    """Lazy import for report service."""
    from ...services.report_service import get_report_service
    return get_report_service()


@tool
async def generate_market_report(
    location: str,
    business_type: str,
    market_size: dict | None = None,
    competitors: dict | None = None,
    financial_summary: dict | None = None,
    swot: dict | None = None,
    sentiment: dict | None = None,
    economic: dict | None = None,
) -> dict[str, Any]:
    """
    Aggregate analysis results into a structured market research report.

    Use this tool when:
    - User asks for a market report
    - User wants a summary of all analysis
    - User says "generate report" or "compile findings"
    - You have completed multiple analyses and need to aggregate them

    Aggregates data from various analysis tools into organized report sections.

    Args:
        location: The location being analyzed
        business_type: Type of business
        market_size: Output from market sizing tools (TAM/SAM/SOM)
        competitors: Output from competitor analysis tools
        financial_summary: Output from financial analysis tools
        swot: Output from SWOT analysis
        sentiment: Output from sentiment analysis
        economic: Output from economic analysis

    Returns:
        Structured report with sections and metadata.

    Example:
        generate_market_report("Austin, TX", "coffee shop", market_size={...}, competitors={...})
    """
    service = _get_report_service()

    analysis_results = {
        "location": location,
        "business_type": business_type,
    }

    if market_size:
        analysis_results["market_size"] = market_size
    if competitors:
        analysis_results["competitors"] = competitors
    if financial_summary:
        analysis_results["financial_summary"] = financial_summary
    if swot:
        analysis_results["swot"] = swot
    if sentiment:
        analysis_results["sentiment"] = sentiment
    if economic:
        analysis_results["economic"] = economic

    report = service.aggregate_report_data(analysis_results)
    report["location"] = location
    report["business_type"] = business_type

    return report


@tool
async def get_executive_summary(
    location: str,
    business_type: str,
    viability_score: float | None = None,
    viability_level: str | None = None,
    tam: float | None = None,
    sam: float | None = None,
    som: float | None = None,
    projected_revenue: float | None = None,
    months_to_break_even: int | None = None,
    competitor_count: int | None = None,
    strengths: list[str] | None = None,
    threats: list[str] | None = None,
    sentiment_label: str | None = None,
    top_pain_points: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate an LLM-powered executive summary with key findings.

    Use this tool when:
    - User asks for executive summary
    - User wants key findings or highlights
    - User says "summarize the analysis"
    - User asks "what are the main takeaways?"

    Generates a concise summary with paragraphs, key findings, and recommendation.

    Args:
        location: The location being analyzed
        business_type: Type of business
        viability_score: Overall viability score (0-100)
        viability_level: Viability level (low/moderate/high)
        tam: Total addressable market value
        sam: Serviceable available market value
        som: Serviceable obtainable market value
        projected_revenue: Projected annual revenue
        months_to_break_even: Months to break even
        competitor_count: Number of competitors found
        strengths: Key strengths from SWOT
        threats: Key threats from SWOT
        sentiment_label: Overall sentiment label
        top_pain_points: Top customer pain points

    Returns:
        Executive summary with paragraphs, key findings, and recommendation.

    Example:
        get_executive_summary("Seattle, WA", "restaurant", viability_score=72, tam=5000000)
    """
    service = _get_report_service()

    # Build report data structure
    report_data = {
        "metadata": {
            "location": location,
            "business_type": business_type,
        },
        "sections": {
            "summary": {
                "viability_score": viability_score,
                "viability_level": viability_level,
                "key_metrics": {},
            },
        },
    }

    # Add key metrics
    if tam is not None:
        report_data["sections"]["summary"]["key_metrics"]["tam"] = tam
    if sam is not None:
        report_data["sections"]["summary"]["key_metrics"]["sam"] = sam
    if som is not None:
        report_data["sections"]["summary"]["key_metrics"]["som"] = som
    if projected_revenue is not None:
        report_data["sections"]["summary"]["key_metrics"]["projected_revenue"] = projected_revenue
    if months_to_break_even is not None:
        report_data["sections"]["summary"]["key_metrics"]["months_to_break_even"] = months_to_break_even

    # Add competition section
    if competitor_count is not None or strengths or threats:
        report_data["sections"]["competition"] = {}
        if competitor_count is not None:
            report_data["sections"]["competition"]["competitor_count"] = competitor_count
        if strengths or threats:
            report_data["sections"]["competition"]["swot"] = {}
            if strengths:
                report_data["sections"]["competition"]["swot"]["strengths"] = [
                    {"factor": s} if isinstance(s, str) else s for s in strengths
                ]
            if threats:
                report_data["sections"]["competition"]["swot"]["threats"] = [
                    {"factor": t} if isinstance(t, str) else t for t in threats
                ]

    # Add consumer insights section
    if sentiment_label or top_pain_points:
        report_data["sections"]["consumer_insights"] = {}
        if sentiment_label:
            report_data["sections"]["consumer_insights"]["sentiment"] = {"label": sentiment_label}
        if top_pain_points:
            report_data["sections"]["consumer_insights"]["top_pain_points"] = [
                {"issue": p} if isinstance(p, str) else p for p in top_pain_points
            ]

    result = await service.generate_executive_summary(report_data)
    result["location"] = location
    result["business_type"] = business_type

    return result


@tool
async def get_key_recommendations(
    location: str,
    business_type: str,
    viability_score: float | None = None,
    viability_level: str | None = None,
    competitor_count: int | None = None,
    months_to_break_even: int | None = None,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    opportunities: list[str] | None = None,
    threats: list[str] | None = None,
    pain_points: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generate prioritized recommendations by category.

    Use this tool when:
    - User asks for recommendations
    - User wants to know "what should I do?"
    - User asks for action items or next steps
    - User wants strategic advice

    Generates prioritized recommendations categorized as immediate actions,
    strategic considerations, and risk mitigations.

    Args:
        location: The location being analyzed
        business_type: Type of business
        viability_score: Overall viability score (0-100)
        viability_level: Viability level (low/moderate/high)
        competitor_count: Number of competitors found
        months_to_break_even: Months to break even
        strengths: Key strengths from SWOT
        weaknesses: Key weaknesses from SWOT
        opportunities: Key opportunities from SWOT
        threats: Key threats from SWOT
        pain_points: Customer pain points

    Returns:
        List of recommendations with title, description, rationale, priority, and category.

    Example:
        get_key_recommendations("Portland, OR", "bakery", viability_score=65, competitor_count=15)
    """
    service = _get_report_service()

    # Build report data structure
    report_data = {
        "metadata": {
            "location": location,
            "business_type": business_type,
        },
        "sections": {
            "summary": {
                "viability_score": viability_score,
                "viability_level": viability_level,
                "key_metrics": {},
            },
        },
    }

    if months_to_break_even is not None:
        report_data["sections"]["summary"]["key_metrics"]["months_to_break_even"] = months_to_break_even

    # Add competition section
    if competitor_count is not None or strengths or weaknesses or opportunities or threats:
        report_data["sections"]["competition"] = {}
        if competitor_count is not None:
            report_data["sections"]["competition"]["competitor_count"] = competitor_count
        if any([strengths, weaknesses, opportunities, threats]):
            report_data["sections"]["competition"]["swot"] = {}
            if strengths:
                report_data["sections"]["competition"]["swot"]["strengths"] = [
                    {"factor": s} if isinstance(s, str) else s for s in strengths
                ]
            if weaknesses:
                report_data["sections"]["competition"]["swot"]["weaknesses"] = [
                    {"factor": w} if isinstance(w, str) else w for w in weaknesses
                ]
            if opportunities:
                report_data["sections"]["competition"]["swot"]["opportunities"] = [
                    {"factor": o} if isinstance(o, str) else o for o in opportunities
                ]
            if threats:
                report_data["sections"]["competition"]["swot"]["threats"] = [
                    {"factor": t} if isinstance(t, str) else t for t in threats
                ]

    # Add consumer insights section
    if pain_points:
        report_data["sections"]["consumer_insights"] = {
            "top_pain_points": [{"issue": p} if isinstance(p, str) else p for p in pain_points]
        }

    recommendations = await service.generate_recommendations(report_data)

    return {
        "location": location,
        "business_type": business_type,
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
        "by_category": {
            "immediate_actions": [r for r in recommendations if r.get("category") == "immediate_actions"],
            "strategic_considerations": [r for r in recommendations if r.get("category") == "strategic_considerations"],
            "risk_mitigations": [r for r in recommendations if r.get("category") == "risk_mitigations"],
        },
        "by_priority": {
            "high": [r for r in recommendations if r.get("priority") == "high"],
            "medium": [r for r in recommendations if r.get("priority") == "medium"],
            "low": [r for r in recommendations if r.get("priority") == "low"],
        },
    }


# List of all report tools
REPORT_TOOLS = [
    generate_market_report,
    get_executive_summary,
    get_key_recommendations,
]
