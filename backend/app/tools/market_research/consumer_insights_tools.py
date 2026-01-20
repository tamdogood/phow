"""LangChain tools for consumer insights and sentiment analysis."""

from typing import Any
from langchain_core.tools import tool


def _get_consumer_analysis_service():
    """Lazy import for consumer analysis service."""
    from ...services.consumer_analysis_service import get_consumer_analysis_service
    return get_consumer_analysis_service()


def _get_maps_client():
    """Lazy import for Google Maps client."""
    from ..location_scout.google_maps import GoogleMapsClient
    return GoogleMapsClient()


def _get_competitor_tools():
    """Lazy import for competitor review analysis."""
    from ..competitor_analyzer.agent_tools import analyze_competitor_reviews
    return analyze_competitor_reviews


@tool
async def analyze_customer_sentiment(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Analyze customer sentiment from competitor reviews in an area.

    Use this tool when:
    - User asks about customer sentiment or satisfaction
    - User wants to understand how customers feel about competitors
    - User asks "What do customers think of X in this area?"
    - User wants sentiment analysis of local market

    Analyzes reviews from competitors to understand overall customer sentiment
    and aspect-level sentiment (service, quality, price, atmosphere, location).

    Args:
        address: The address to search around
        business_type: Type of business

    Returns:
        Sentiment analysis with overall score and aspect breakdown.

    Example:
        analyze_customer_sentiment("Capitol Hill, Seattle", "coffee shop")
    """
    service = _get_consumer_analysis_service()

    # Get reviews from competitors
    reviews = await _gather_competitor_reviews(address, business_type)

    if not reviews:
        return {
            "error": "No reviews found in the area",
            "location": address,
            "business_type": business_type,
        }

    result = service.analyze_sentiment(reviews)
    result["location"] = address
    result["business_type"] = business_type

    return result


@tool
async def extract_customer_themes(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Extract common themes from customer reviews in an area.

    Use this tool when:
    - User asks what customers talk about
    - User wants to know common topics in reviews
    - User asks "What do people say about X?"
    - User wants theme extraction from reviews

    Extracts positive and negative themes from competitor reviews,
    grouped by category (product, service, experience, value, location).

    Args:
        address: The address to search around
        business_type: Type of business

    Returns:
        Themes grouped by category with frequency and sentiment.

    Example:
        extract_customer_themes("Downtown Portland, OR", "restaurant")
    """
    service = _get_consumer_analysis_service()

    # Get reviews from competitors
    reviews = await _gather_competitor_reviews(address, business_type)

    if not reviews:
        return {
            "error": "No reviews found in the area",
            "location": address,
            "business_type": business_type,
        }

    result = service.extract_themes(reviews)
    result["location"] = address
    result["business_type"] = business_type

    return result


@tool
async def identify_customer_pain_points(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Identify customer pain points from competitor reviews.

    Use this tool when:
    - User asks about customer complaints or problems
    - User wants to know what frustrates customers
    - User asks "What are the pain points?"
    - User wants to find differentiation opportunities

    Identifies and ranks pain points from negative reviews, with
    opportunities for differentiation based on competitor weaknesses.

    Args:
        address: The address to search around
        business_type: Type of business

    Returns:
        Ranked pain points with frequency, severity, and opportunities.

    Example:
        identify_customer_pain_points("SoMa, San Francisco", "gym")
    """
    service = _get_consumer_analysis_service()

    # Get reviews from competitors
    reviews = await _gather_competitor_reviews(address, business_type)

    if not reviews:
        return {
            "error": "No reviews found in the area",
            "location": address,
            "business_type": business_type,
        }

    result = service.identify_pain_points(reviews)
    result["location"] = address
    result["business_type"] = business_type

    return result


@tool
async def map_customer_journey(
    business_type: str,
    address: str | None = None,
) -> dict[str, Any]:
    """
    Map the typical customer journey for a business type.

    Use this tool when:
    - User asks about customer journey or experience
    - User wants to understand touchpoints
    - User asks "How do customers interact with X?"
    - User wants journey mapping for their business

    Maps the 5 stages of customer journey: awareness, consideration,
    purchase, experience, and loyalty. Includes touchpoints and
    opportunities at each stage.

    Args:
        business_type: Type of business
        address: Optional address to analyze local competitor reviews

    Returns:
        Customer journey map with stages, touchpoints, and opportunities.

    Example:
        map_customer_journey("bakery", "Brooklyn, NY")
    """
    service = _get_consumer_analysis_service()

    reviews = None
    if address:
        reviews = await _gather_competitor_reviews(address, business_type)

    result = service.map_customer_journey(business_type, reviews)
    if address:
        result["location"] = address

    return result


@tool
async def build_customer_profile(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Build a psychographic customer profile for the target market.

    Use this tool when:
    - User asks about target customers
    - User wants customer persona or profile
    - User asks "Who are my customers?"
    - User wants targeting recommendations

    Builds a customer profile combining demographics with behavioral
    insights from reviews. Includes values, preferences, price sensitivity,
    and marketing recommendations.

    Args:
        address: The address for the target market
        business_type: Type of business

    Returns:
        Customer profile with persona, insights, and targeting recommendations.

    Example:
        build_customer_profile("Austin, TX", "yoga studio")
    """
    service = _get_consumer_analysis_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Try to get demographics
    demographics = {}
    try:
        from ..market_validator.census_client import CensusClient
        census = CensusClient()
        demographics = await census.get_demographics(location["lat"], location["lng"])
    except Exception:
        # Use default demographics if unavailable
        demographics = {
            "median_income": 60000,
            "total_population": 50000,
            "age_distribution": {"25-44": 35, "45-64": 30, "18-24": 20},
        }

    # Get reviews for behavioral insights
    reviews = await _gather_competitor_reviews(address, business_type)

    return service.build_consumer_profile(location, business_type, demographics, reviews)


@tool
async def get_consumer_insights_summary(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Get comprehensive consumer insights combining sentiment, themes,
    pain points, and customer profile.

    Use this tool for a complete consumer analysis that includes:
    - Sentiment analysis with aspect breakdown
    - Theme extraction
    - Pain points and opportunities
    - Customer profile and targeting recommendations

    Args:
        address: The address for analysis
        business_type: Type of business

    Returns:
        Comprehensive consumer insights summary.

    Example:
        get_consumer_insights_summary("Chicago, IL", "pizza restaurant")
    """
    service = _get_consumer_analysis_service()
    maps_client = _get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    location["address"] = address

    # Gather reviews
    reviews = await _gather_competitor_reviews(address, business_type)

    if not reviews:
        return {
            "error": "No reviews found for analysis",
            "location": address,
            "business_type": business_type,
        }

    # Run all analyses
    sentiment = service.analyze_sentiment(reviews)
    themes = service.extract_themes(reviews)
    pain_points = service.identify_pain_points(reviews)
    journey = service.map_customer_journey(business_type, reviews)

    # Try to get demographics for profile
    demographics = {}
    try:
        from ..market_validator.census_client import CensusClient
        census = CensusClient()
        demographics = await census.get_demographics(location["lat"], location["lng"])
    except Exception:
        demographics = {"median_income": 60000, "total_population": 50000}

    profile = service.build_consumer_profile(location, business_type, demographics, reviews)

    # Generate key insights
    insights = _generate_consumer_insights(sentiment, themes, pain_points)

    return {
        "location": address,
        "business_type": business_type,
        "reviews_analyzed": len(reviews),
        "sentiment_summary": {
            "overall": sentiment.get("sentiment_label"),
            "score": sentiment.get("overall_sentiment"),
            "top_aspects": list(sentiment.get("aspect_sentiments", {}).keys())[:3],
        },
        "top_themes": {
            "positive": [t["theme"] for t in themes.get("themes", []) if t.get("sentiment") == "positive"][:3],
            "negative": [t["theme"] for t in themes.get("themes", []) if t.get("sentiment") == "negative"][:3],
        },
        "top_pain_points": [pp["issue"] for pp in pain_points.get("pain_points", [])[:3]],
        "opportunities": pain_points.get("opportunities", [])[:3],
        "target_customer": profile.get("primary_persona", {}),
        "key_insights": insights,
        "full_sentiment": sentiment,
        "full_themes": themes,
        "full_pain_points": pain_points,
    }


async def _gather_competitor_reviews(address: str, business_type: str) -> list[dict]:
    """Gather reviews from competitors in the area."""
    try:
        analyze_reviews_tool = _get_competitor_tools()
        result = await analyze_reviews_tool.ainvoke({
            "address": address,
            "business_type": business_type,
        })

        if "error" in result:
            return []

        # Extract reviews from competitors
        reviews = []
        for comp in result.get("competitors", []):
            sample_reviews = comp.get("sample_reviews", [])
            for review_text in sample_reviews:
                reviews.append({
                    "text": review_text,
                    "rating": comp.get("rating", 3),
                    "source": comp.get("name", "competitor"),
                })

        return reviews

    except Exception:
        return []


def _generate_consumer_insights(
    sentiment: dict,
    themes: dict,
    pain_points: dict,
) -> list[str]:
    """Generate key insights from consumer analysis."""
    insights = []

    # Sentiment insight
    sentiment_label = sentiment.get("sentiment_label", "neutral")
    if sentiment_label == "positive":
        insights.append("Overall customer satisfaction is high - quality bar is set high in this market")
    elif sentiment_label == "negative":
        insights.append("Customer satisfaction is low - opportunity to differentiate through quality")

    # Theme insight
    positive_themes = [t["theme"] for t in themes.get("themes", []) if t.get("sentiment") == "positive"][:2]
    if positive_themes:
        insights.append(f"Customers value: {', '.join(positive_themes)} - match or exceed these expectations")

    # Pain point insight
    top_pain_points = pain_points.get("pain_points", [])[:2]
    if top_pain_points:
        issues = [pp["issue"].lower() for pp in top_pain_points]
        insights.append(f"Address competitor weaknesses: {', '.join(issues)}")

    # Opportunity insight
    opportunities = pain_points.get("opportunities", [])
    if opportunities:
        insights.append(f"Key opportunity: {opportunities[0].get('recommendation', 'Differentiate through quality')}")

    return insights if insights else ["Focus on consistent quality and excellent customer service"]


# List of all consumer insights tools
CONSUMER_INSIGHTS_TOOLS = [
    analyze_customer_sentiment,
    extract_customer_themes,
    identify_customer_pain_points,
    map_customer_journey,
    build_customer_profile,
    get_consumer_insights_summary,
]
