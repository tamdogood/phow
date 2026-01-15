"""LangChain tools for Competitor Analyzer agent."""

import asyncio
import re
from typing import Any
from langchain_core.tools import tool
from .yelp_client import get_yelp_client
from ..location_scout.google_maps import GoogleMapsClient
from ...core.logging import get_logger

logger = get_logger("competitor_analyzer.tools")

# Shared clients
_maps_client: GoogleMapsClient | None = None


def get_maps_client() -> GoogleMapsClient:
    """Get or create the Google Maps client."""
    global _maps_client
    if _maps_client is None:
        _maps_client = GoogleMapsClient()
    return _maps_client


@tool
async def find_competitors(
    address: str,
    business_type: str,
    radius_meters: int = 1500,
) -> dict[str, Any]:
    """
    Find all competitors of a specific business type near an address.

    This is the primary tool for discovering competitors. It combines data from
    Google Maps and Yelp to provide comprehensive competitor information.

    Args:
        address: The address to search around
        business_type: Type of business to find (e.g., "coffee shop", "gym", "restaurant")
        radius_meters: Search radius in meters (default 1500m)

    Returns:
        List of competitors with details including ratings, reviews, pricing, and categories
    """
    maps_client = get_maps_client()
    yelp_client = get_yelp_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]
    logger.info("Finding competitors", lat=lat, lng=lng, business_type=business_type)

    # Get competitors from Google Maps and Yelp in parallel
    google_competitors, yelp_competitors = await asyncio.gather(
        maps_client.nearby_search(lat=lat, lng=lng, radius=radius_meters, keyword=business_type),
        yelp_client.search_businesses(
            term=business_type,
            latitude=lat,
            longitude=lng,
            radius=radius_meters,
            sort_by="distance",
        ),
    )

    # Merge and deduplicate based on name similarity
    competitors = _merge_competitors(google_competitors, yelp_competitors)

    return {
        "location": location,
        "business_type": business_type,
        "radius_meters": radius_meters,
        "total_found": len(competitors),
        "competitors": competitors[:15],  # Limit to top 15
        "sources": {
            "google": len(google_competitors),
            "yelp": len(yelp_competitors),
        },
    }


@tool
async def get_competitor_details(
    competitor_name: str,
    address: str,
) -> dict[str, Any]:
    """
    Get detailed information about a specific competitor.

    Use this when you need more information about a particular competitor,
    including their reviews, hours, and services.

    Args:
        competitor_name: Name of the competitor business
        address: Address near the competitor (for finding the right one)

    Returns:
        Detailed competitor information including reviews, hours, and services
    """
    maps_client = get_maps_client()
    yelp_client = get_yelp_client()

    # Geocode to get coordinates
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Search for the specific competitor
    google_results = await maps_client.nearby_search(
        lat=lat,
        lng=lng,
        radius=1000,
        keyword=competitor_name,
    )

    # Find the best match
    best_match = None
    for result in google_results:
        if _name_similarity(result.get("name", ""), competitor_name) > 0.7:
            best_match = result
            break

    if not best_match:
        return {"error": f"Could not find competitor: {competitor_name}"}

    # Get Google Place details
    place_details = {}
    if best_match.get("place_id"):
        place_details = await maps_client.get_place_details(best_match["place_id"]) or {}

    # Try to find on Yelp for additional info
    yelp_results = await yelp_client.search_businesses(
        term=competitor_name,
        latitude=lat,
        longitude=lng,
        radius=500,
        limit=5,
    )

    yelp_match = None
    for result in yelp_results:
        if _name_similarity(result.get("name", ""), competitor_name) > 0.7:
            yelp_match = result
            break

    # Get Yelp reviews if we found a match
    yelp_reviews = []
    if yelp_match and yelp_match.get("id"):
        yelp_reviews = await yelp_client.get_business_reviews(yelp_match["id"])

    return {
        "name": best_match.get("name"),
        "address": place_details.get("formatted_address") or best_match.get("vicinity"),
        "rating": {
            "google": best_match.get("rating"),
            "yelp": yelp_match.get("rating") if yelp_match else None,
        },
        "review_count": {
            "google": best_match.get("user_ratings_total"),
            "yelp": yelp_match.get("review_count") if yelp_match else None,
        },
        "price_level": {
            "google": best_match.get("price_level"),
            "yelp": yelp_match.get("price") if yelp_match else None,
        },
        "categories": yelp_match.get("categories", []) if yelp_match else [],
        "phone": place_details.get("formatted_phone_number"),
        "website": place_details.get("website"),
        "hours": place_details.get("opening_hours", {}).get("weekday_text", []),
        "reviews": place_details.get("reviews", [])[:3] + yelp_reviews,
        "yelp_url": yelp_match.get("url") if yelp_match else None,
    }


@tool
async def analyze_competitor_reviews(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Analyze reviews of competitors to identify strengths and weaknesses.

    This tool extracts common themes from competitor reviews to help identify
    opportunities for differentiation.

    Args:
        address: The address to search around
        business_type: Type of business

    Returns:
        Analysis of competitor strengths and weaknesses based on reviews
    """
    maps_client = get_maps_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Find competitors
    competitors = await maps_client.nearby_search(
        lat=lat,
        lng=lng,
        radius=1500,
        keyword=business_type,
    )

    # Analyze reviews from top competitors (fetch details in parallel)
    all_reviews = []
    analyzed_competitors = []

    # Get competitors with place_ids
    competitors_with_ids = [c for c in competitors[:5] if c.get("place_id")]

    # Fetch all place details in parallel
    if competitors_with_ids:
        details_list = await asyncio.gather(
            *[maps_client.get_place_details(c["place_id"]) for c in competitors_with_ids]
        )

        # Process results
        for comp, details in zip(competitors_with_ids, details_list):
            if details and details.get("reviews"):
                reviews = details["reviews"][:5]
                all_reviews.extend(reviews)
                analyzed_competitors.append(
                    {
                        "name": comp.get("name"),
                        "rating": comp.get("rating"),
                        "review_count": comp.get("user_ratings_total"),
                        "sample_reviews": [r.get("text", "")[:200] for r in reviews[:2]],
                    }
                )

    # Extract themes from reviews
    themes = _extract_review_themes(all_reviews)

    return {
        "location": location,
        "business_type": business_type,
        "competitors_analyzed": len(analyzed_competitors),
        "total_reviews_analyzed": len(all_reviews),
        "competitors": analyzed_competitors,
        "common_themes": themes,
        "insights": {
            "strengths": themes.get("positive_themes", []),
            "weaknesses": themes.get("negative_themes", []),
            "opportunities": _identify_opportunities(themes),
        },
    }


@tool
async def create_positioning_map(
    address: str,
    business_type: str,
) -> dict[str, Any]:
    """
    Create a competitive positioning map based on price and quality.

    This visualizes where competitors sit in terms of price level vs. rating,
    helping identify market gaps and positioning opportunities.

    Args:
        address: The address to search around
        business_type: Type of business

    Returns:
        Positioning data for all competitors with quadrant analysis
    """
    maps_client = get_maps_client()
    yelp_client = get_yelp_client()

    # Geocode the address
    location = await maps_client.geocode(address)
    if not location:
        return {"error": f"Could not find address: {address}"}

    lat, lng = location["lat"], location["lng"]

    # Get competitors from both sources in parallel
    google_competitors, yelp_competitors = await asyncio.gather(
        maps_client.nearby_search(lat=lat, lng=lng, radius=1500, keyword=business_type),
        yelp_client.search_businesses(term=business_type, latitude=lat, longitude=lng, radius=1500),
    )

    # Merge competitors
    competitors = _merge_competitors(google_competitors, yelp_competitors)

    # Create positioning data
    positioning_data = []
    for comp in competitors:
        rating = comp.get("rating")
        price = comp.get("price_level") or _price_string_to_level(comp.get("yelp_price"))

        if rating and price:
            positioning_data.append(
                {
                    "name": comp.get("name"),
                    "rating": rating,
                    "price_level": price,
                    "review_count": comp.get("review_count", 0),
                    "quadrant": _determine_quadrant(price, rating),
                }
            )

    # Analyze quadrants
    quadrant_counts = {"premium": 0, "value": 0, "economy": 0, "avoid": 0}
    for p in positioning_data:
        quadrant_counts[p["quadrant"]] += 1

    # Find gaps
    gaps = []
    if quadrant_counts["premium"] < 2:
        gaps.append("Premium segment (high quality, higher prices) has few competitors")
    if quadrant_counts["value"] < 2:
        gaps.append("Value segment (high quality, moderate prices) has opportunities")
    if quadrant_counts["economy"] < 2:
        gaps.append("Budget segment (moderate quality, low prices) is underserved")

    return {
        "location": location,
        "business_type": business_type,
        "total_competitors": len(positioning_data),
        "positioning_data": positioning_data,
        "quadrant_analysis": quadrant_counts,
        "market_gaps": gaps,
        "recommendation": _get_positioning_recommendation(quadrant_counts, positioning_data),
    }


def _merge_competitors(google: list, yelp: list) -> list[dict]:
    """Merge competitors from Google and Yelp, deduplicating by name."""
    merged = {}

    # Add Google results first
    for comp in google:
        name = comp.get("name", "").lower().strip()
        merged[name] = {
            "name": comp.get("name"),
            "rating": comp.get("rating"),
            "review_count": comp.get("user_ratings_total", 0),
            "address": comp.get("vicinity"),
            "price_level": comp.get("price_level"),
            "place_id": comp.get("place_id"),
            "source": "google",
        }

    # Merge Yelp results
    for comp in yelp:
        name = comp.get("name", "").lower().strip()
        if name in merged:
            # Add Yelp data to existing entry
            merged[name]["yelp_rating"] = comp.get("rating")
            merged[name]["yelp_review_count"] = comp.get("review_count")
            merged[name]["yelp_price"] = comp.get("price")
            merged[name]["categories"] = comp.get("categories", [])
            merged[name]["source"] = "both"
        else:
            merged[name] = {
                "name": comp.get("name"),
                "rating": comp.get("rating"),
                "review_count": comp.get("review_count", 0),
                "address": comp.get("address"),
                "yelp_price": comp.get("price"),
                "categories": comp.get("categories", []),
                "source": "yelp",
            }

    # Sort by review count (most reviewed first)
    competitors = sorted(
        merged.values(),
        key=lambda x: x.get("review_count", 0),
        reverse=True,
    )

    return competitors


def _name_similarity(name1: str, name2: str) -> float:
    """Calculate simple name similarity."""
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()

    if name1 == name2:
        return 1.0

    # Check if one contains the other
    if name1 in name2 or name2 in name1:
        return 0.8

    # Simple word overlap
    words1 = set(name1.split())
    words2 = set(name2.split())
    overlap = len(words1 & words2)
    total = len(words1 | words2)

    return overlap / total if total > 0 else 0.0


def _extract_review_themes(reviews: list[dict]) -> dict:
    """Extract common themes from reviews."""
    positive_keywords = [
        "friendly",
        "fast",
        "clean",
        "fresh",
        "quality",
        "delicious",
        "great service",
        "love",
        "best",
        "amazing",
        "excellent",
        "convenient",
        "atmosphere",
        "cozy",
        "recommend",
    ]
    negative_keywords = [
        "slow",
        "rude",
        "dirty",
        "expensive",
        "overpriced",
        "cold",
        "wait",
        "crowded",
        "small",
        "noisy",
        "disappointing",
        "mediocre",
        "average",
        "poor service",
    ]

    positive_found = {}
    negative_found = {}

    for review in reviews:
        text = review.get("text", "").lower()
        rating = review.get("rating", 3)

        for keyword in positive_keywords:
            if keyword in text:
                positive_found[keyword] = positive_found.get(keyword, 0) + 1

        for keyword in negative_keywords:
            if keyword in text:
                negative_found[keyword] = negative_found.get(keyword, 0) + 1

    # Sort by frequency
    positive_themes = sorted(positive_found.items(), key=lambda x: x[1], reverse=True)[:5]
    negative_themes = sorted(negative_found.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "positive_themes": [t[0] for t in positive_themes],
        "negative_themes": [t[0] for t in negative_themes],
    }


def _identify_opportunities(themes: dict) -> list[str]:
    """Identify opportunities based on review themes."""
    opportunities = []

    negative = themes.get("negative_themes", [])
    if "slow" in negative or "wait" in negative:
        opportunities.append(
            "Fast service could be a differentiator - competitors have wait time issues"
        )
    if "expensive" in negative or "overpriced" in negative:
        opportunities.append("Value pricing could attract price-sensitive customers")
    if "dirty" in negative:
        opportunities.append("Cleanliness and hygiene could set you apart")
    if "rude" in negative or "poor service" in negative:
        opportunities.append("Excellent customer service would be a competitive advantage")

    return opportunities if opportunities else ["Focus on overall quality and consistency"]


def _price_string_to_level(price_str: str | None) -> int | None:
    """Convert Yelp price string ($, $$, etc.) to numeric level."""
    if not price_str:
        return None
    return len(price_str)  # $ = 1, $$ = 2, $$$ = 3, $$$$ = 4


def _determine_quadrant(price: int, rating: float) -> str:
    """Determine market quadrant based on price and rating."""
    high_quality = rating >= 4.0
    high_price = price >= 3

    if high_quality and high_price:
        return "premium"
    elif high_quality and not high_price:
        return "value"
    elif not high_quality and not high_price:
        return "economy"
    else:
        return "avoid"  # High price, low quality


def _get_positioning_recommendation(quadrants: dict, data: list) -> str:
    """Get strategic positioning recommendation."""
    # Find the quadrant with least competition
    min_quadrant = min(quadrants, key=quadrants.get)

    recommendations = {
        "premium": "Consider a premium positioning with higher quality and prices - this segment has room for competition",
        "value": "A value positioning (high quality, moderate prices) could capture significant market share",
        "economy": "The budget segment is underserved - lower prices with decent quality could attract cost-conscious customers",
        "avoid": "Focus on either improving quality or lowering prices - the high-price/low-quality segment is risky",
    }

    return recommendations.get(min_quadrant, "Focus on differentiation through unique offerings")


# List of all tools for the agent
COMPETITOR_ANALYZER_TOOLS = [
    find_competitors,
    get_competitor_details,
    analyze_competitor_reviews,
    create_positioning_map,
]
