"""LangChain tools for the Social Media Coach agent."""

import json
from datetime import datetime
from typing import Any
from langchain_core.tools import tool

from .weather_client import WeatherClient
from .events_client import EventsClient
from ..location_scout.google_maps import GoogleMapsClient
from ...core.logging import get_logger

logger = get_logger("social_media_coach.tools")

# Initialize clients
weather_client = WeatherClient()
events_client = EventsClient()
maps_client = GoogleMapsClient()


@tool
async def get_location_context(address: str) -> str:
    """Get location coordinates and basic info for content generation.

    Args:
        address: The business address to analyze

    Returns:
        Location context including coordinates and city name
    """
    logger.info("Getting location context", address=address)

    location = await maps_client.geocode(address)
    if not location:
        return json.dumps({"error": "Could not geocode address"})

    return json.dumps({
        "lat": location["lat"],
        "lng": location["lng"],
        "formatted_address": location["formatted_address"],
        "city": location["formatted_address"].split(",")[1].strip() if "," in location["formatted_address"] else "Unknown",
    })


@tool
async def get_weather_and_impact(lat: float, lng: float, business_type: str) -> str:
    """Get current weather and analyze its impact on business content.

    Args:
        lat: Latitude of the business location
        lng: Longitude of the business location
        business_type: Type of business (e.g., "coffee shop", "restaurant")

    Returns:
        Weather data with business impact analysis and content angles
    """
    logger.info("Getting weather and impact", lat=lat, lng=lng, business_type=business_type)

    weather = await weather_client.get_current_weather(lat, lng)
    if not weather:
        return json.dumps({"error": "Could not retrieve weather data"})

    impact = weather_client.get_weather_impact(weather, business_type)

    return json.dumps({
        "weather": weather,
        "impact": impact,
    })


@tool
async def get_upcoming_events_and_holidays(lat: float, lng: float, days_ahead: int = 14) -> str:
    """Get upcoming local events and holidays for content opportunities.

    Args:
        lat: Latitude of the business location
        lng: Longitude of the business location
        days_ahead: Number of days to look ahead (default 14)

    Returns:
        List of upcoming events and holidays with content opportunities
    """
    logger.info("Getting events and holidays", lat=lat, lng=lng, days_ahead=days_ahead)

    holidays = events_client.get_upcoming_holidays(days_ahead)
    local_events = await events_client.get_local_events(lat, lng, days_ahead=days_ahead)
    daily_themes = events_client.get_daily_themes()

    opportunities = events_client.get_content_opportunities(
        business_type="general",  # Will be refined by the agent
        holidays=holidays,
        events=local_events,
        daily_themes=daily_themes,
    )

    return json.dumps({
        "daily_themes": daily_themes,
        "upcoming_holidays": holidays,
        "local_events": local_events,
        "content_opportunities": opportunities,
    })


@tool
def get_trending_hashtags(business_type: str, city: str) -> str:
    """Get trending and relevant hashtags for the business.

    Args:
        business_type: Type of business (e.g., "coffee shop", "restaurant")
        city: City name for local hashtags

    Returns:
        List of recommended hashtags organized by category
    """
    logger.info("Getting trending hashtags", business_type=business_type, city=city)

    # General business hashtags
    general = ["#SmallBusiness", "#SupportLocal", "#ShopSmall", "#LocalBusiness"]

    # Day-based hashtags
    today = datetime.now()
    day_hashtags = {
        0: ["#MondayMotivation", "#NewWeek", "#MondayMood"],
        1: ["#TuesdayThoughts", "#TipTuesday", "#TransformationTuesday"],
        2: ["#WednesdayWisdom", "#HumpDay", "#MidweekMotivation"],
        3: ["#ThrowbackThursday", "#TBT", "#ThursdayThoughts"],
        4: ["#FridayFeeling", "#TGIF", "#FridayVibes"],
        5: ["#SmallBusinessSaturday", "#SaturdayVibes", "#WeekendMode"],
        6: ["#SundayFunday", "#SelfCareSunday", "#SundayVibes"],
    }

    # Business-type specific hashtags
    business_lower = business_type.lower()
    type_hashtags = []

    if "coffee" in business_lower or "cafe" in business_lower:
        type_hashtags = ["#CoffeeLovers", "#CoffeeTime", "#ButFirstCoffee", "#CoffeeShop", "#Barista"]
    elif "restaurant" in business_lower or "food" in business_lower:
        type_hashtags = ["#Foodie", "#FoodLover", "#Instafood", "#LocalEats", "#FoodPorn"]
    elif "bakery" in business_lower or "bake" in business_lower:
        type_hashtags = ["#BakeryLife", "#FreshBaked", "#HomeMade", "#BakingLove", "#Pastry"]
    elif "retail" in business_lower or "shop" in business_lower:
        type_hashtags = ["#RetailTherapy", "#ShoppingTime", "#NewArrivals", "#ShopLocal"]
    elif "gym" in business_lower or "fitness" in business_lower:
        type_hashtags = ["#FitnessMotivation", "#GymLife", "#WorkoutTime", "#FitFam"]
    elif "salon" in business_lower or "beauty" in business_lower:
        type_hashtags = ["#BeautyTips", "#SalonLife", "#HairGoals", "#BeautyRoutine"]
    elif "auto" in business_lower or "car" in business_lower:
        type_hashtags = ["#CarCare", "#AutoService", "#CarLife", "#DriveHappy"]
    else:
        type_hashtags = ["#Entrepreneur", "#BusinessOwner", "#Success", "#Hustle"]

    # City hashtags
    city_clean = city.replace(" ", "").replace(",", "")
    city_hashtags = [f"#{city_clean}", f"#{city_clean}Local", f"#{city_clean}Business"]

    return json.dumps({
        "general": general,
        "today": day_hashtags.get(today.weekday(), []),
        "business_type": type_hashtags,
        "location": city_hashtags,
        "recommended_count": "Use 3-5 hashtags for best engagement",
    })


@tool
def generate_post_ideas(
    business_type: str,
    weather_description: str,
    upcoming_events: list[str],
    daily_theme: str,
    tone: str = "professional",
) -> str:
    """Generate social media post ideas based on context.

    Args:
        business_type: Type of business
        weather_description: Current weather description
        upcoming_events: List of upcoming events/holidays
        daily_theme: Today's content theme (e.g., "Motivation Monday")
        tone: Desired tone (professional, casual, fun)

    Returns:
        3-5 post ideas with captions ready to use
    """
    logger.info("Generating post ideas", business_type=business_type, tone=tone)

    # This tool provides structure for the LLM to generate creative content
    # The actual content will be generated by the LLM using this context

    return json.dumps({
        "context": {
            "business_type": business_type,
            "weather": weather_description,
            "events": upcoming_events,
            "theme": daily_theme,
            "tone": tone,
        },
        "instructions": """Generate 3-5 social media post ideas. For each idea include:
1. A compelling caption (2-3 sentences max)
2. Suggested hashtags (3-5 relevant ones)
3. Best platform (Instagram, Facebook, Twitter/X)
4. Suggested posting time

Make posts authentic, engaging, and specific to the business context provided.
Vary the post types: promotional, engaging, educational, behind-the-scenes.""",
    })


@tool
def get_best_posting_times(business_type: str) -> str:
    """Get recommended posting times for the business type.

    Args:
        business_type: Type of business

    Returns:
        Recommended posting times by platform
    """
    logger.info("Getting best posting times", business_type=business_type)

    # General best times based on industry research
    business_lower = business_type.lower()

    if "restaurant" in business_lower or "food" in business_lower or "coffee" in business_lower:
        times = {
            "instagram": ["7-9 AM (breakfast content)", "11 AM-1 PM (lunch rush)", "5-7 PM (dinner time)"],
            "facebook": ["11 AM-1 PM", "7-9 PM"],
            "twitter": ["12 PM", "5 PM"],
            "reasoning": "Food businesses should post when people are thinking about meals",
        }
    elif "retail" in business_lower or "shop" in business_lower:
        times = {
            "instagram": ["10 AM-12 PM", "7-9 PM"],
            "facebook": ["1-4 PM", "8 PM"],
            "twitter": ["12-1 PM", "5 PM"],
            "reasoning": "Retail posts perform well during lunch breaks and evening browsing",
        }
    elif "fitness" in business_lower or "gym" in business_lower:
        times = {
            "instagram": ["5-7 AM (morning motivation)", "5-7 PM (after work)"],
            "facebook": ["6-8 AM", "5-7 PM"],
            "twitter": ["6 AM", "12 PM"],
            "reasoning": "Fitness content aligns with workout schedules",
        }
    else:
        times = {
            "instagram": ["11 AM-1 PM", "7-9 PM"],
            "facebook": ["1-4 PM"],
            "twitter": ["12-1 PM", "5-6 PM"],
            "reasoning": "General business hours and evening engagement times",
        }

    times["general_tips"] = [
        "Post consistently - same time each day builds audience expectations",
        "Test and iterate - check your insights for what works",
        "Avoid posting during major events when attention is elsewhere",
    ]

    return json.dumps(times)


# Export all tools for the agent
SOCIAL_MEDIA_COACH_TOOLS = [
    get_location_context,
    get_weather_and_impact,
    get_upcoming_events_and_holidays,
    get_trending_hashtags,
    generate_post_ideas,
    get_best_posting_times,
]
