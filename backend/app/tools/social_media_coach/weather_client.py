"""OpenWeatherMap API client for weather data."""

import httpx
from typing import Any
from datetime import datetime
from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.cache import cached

logger = get_logger("weather_client")


class WeatherClient:
    """Client for OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"
    _client: httpx.AsyncClient | None = None

    def __init__(self):
        settings = get_settings()
        self.api_key = getattr(settings, "openweathermap_api_key", None)

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create a reusable httpx client."""
        if WeatherClient._client is None:
            WeatherClient._client = httpx.AsyncClient()
        return WeatherClient._client

    @cached(ttl=1800, key_prefix="weather")  # Cache for 30 minutes
    async def get_current_weather(self, lat: float, lng: float) -> dict[str, Any] | None:
        """Get current weather for a location."""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured, using mock data")
            return self._get_mock_weather()

        logger.info("Getting current weather", lat=lat, lng=lng)
        try:
            response = await self._get_client().get(
                f"{self.BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lng,
                    "appid": self.api_key,
                    "units": "imperial",  # Fahrenheit
                },
            )
            data = response.json()

            if response.status_code == 200:
                weather = {
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "icon": data["weather"][0]["icon"],
                    "main": data["weather"][0]["main"],
                    "wind_speed": round(data["wind"]["speed"]),
                    "city": data.get("name", "Unknown"),
                }
                logger.info("Weather retrieved", city=weather["city"], temp=weather["temperature"])
                return weather
            logger.warning("Weather API error", status_code=response.status_code)
            return self._get_mock_weather()
        except Exception as e:
            logger.error("Weather API exception", error=str(e))
            return self._get_mock_weather()

    @cached(ttl=3600, key_prefix="forecast")  # Cache for 1 hour
    async def get_forecast(self, lat: float, lng: float, days: int = 5) -> list[dict[str, Any]]:
        """Get weather forecast for next few days."""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured, using mock forecast")
            return self._get_mock_forecast(days)

        logger.info("Getting weather forecast", lat=lat, lng=lng, days=days)
        try:
            response = await self._get_client().get(
                f"{self.BASE_URL}/forecast",
                params={
                    "lat": lat,
                    "lon": lng,
                    "appid": self.api_key,
                    "units": "imperial",
                    "cnt": days * 8,  # 3-hour intervals, 8 per day
                },
            )
            data = response.json()

            if response.status_code == 200:
                # Group by day and get daily summary
                daily_forecasts = []
                seen_dates = set()

                for item in data.get("list", []):
                    date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                    if date not in seen_dates and len(daily_forecasts) < days:
                        seen_dates.add(date)
                        daily_forecasts.append(
                            {
                                "date": date,
                                "day_name": datetime.fromtimestamp(item["dt"]).strftime("%A"),
                                "temperature": round(item["main"]["temp"]),
                                "temp_min": round(item["main"]["temp_min"]),
                                "temp_max": round(item["main"]["temp_max"]),
                                "description": item["weather"][0]["description"],
                                "main": item["weather"][0]["main"],
                                "icon": item["weather"][0]["icon"],
                            }
                        )

                logger.info("Forecast retrieved", days=len(daily_forecasts))
                return daily_forecasts
            logger.warning("Forecast API error", status_code=response.status_code)
            return self._get_mock_forecast(days)
        except Exception as e:
            logger.error("Forecast API exception", error=str(e))
            return self._get_mock_forecast(days)

    def get_weather_impact(self, weather: dict[str, Any], business_type: str) -> dict[str, Any]:
        """Analyze weather impact on business and suggest content angles."""
        temp = weather.get("temperature", 70)
        main = weather.get("main", "Clear").lower()
        description = weather.get("description", "")

        impacts = []
        opportunities = []
        content_angles = []

        # Temperature-based impacts
        if temp >= 80:
            impacts.append("Hot weather - customers may seek cool spaces")
            opportunities.append("Promote air conditioning, cold drinks, or refreshing options")
            content_angles.append("Beat the heat messaging")
        elif temp >= 70:
            impacts.append("Pleasant weather - great for outdoor activities")
            opportunities.append("Highlight outdoor seating, patio, or outdoor-friendly products")
            content_angles.append("Perfect weather for...")
        elif temp >= 50:
            impacts.append("Mild weather - comfortable for most activities")
            content_angles.append("Seasonal transition content")
        else:
            impacts.append("Cold weather - customers seek warmth")
            opportunities.append("Promote warm drinks, cozy atmosphere, comfort items")
            content_angles.append("Warm up with...")

        # Condition-based impacts
        if "rain" in main or "rain" in description:
            impacts.append("Rainy conditions may reduce foot traffic")
            opportunities.append("Promote delivery, takeout, or rainy day specials")
            content_angles.append("Rainy day comfort")
        elif "snow" in main or "snow" in description:
            impacts.append("Snow may significantly reduce foot traffic")
            opportunities.append("Offer delivery or pickup incentives")
            content_angles.append("Snow day specials")
        elif "clear" in main or "sunny" in description:
            opportunities.append("Great day for outdoor photos and location posts")
            content_angles.append("Beautiful day showcase")

        # Business-specific suggestions
        business_lower = business_type.lower()
        if "coffee" in business_lower or "cafe" in business_lower:
            if temp < 60:
                content_angles.append("Hot coffee/cocoa season")
            else:
                content_angles.append("Iced coffee weather")
        elif "restaurant" in business_lower or "food" in business_lower:
            if "rain" in main:
                content_angles.append("Comfort food messaging")
            elif temp >= 75:
                content_angles.append("Light, fresh menu highlights")
        elif "retail" in business_lower or "shop" in business_lower:
            if temp >= 70 and "clear" in main:
                content_angles.append("Window shopping weather")

        return {
            "impacts": impacts,
            "opportunities": opportunities,
            "content_angles": content_angles,
            "is_good_for_outdoor": temp >= 60 and "rain" not in main and "snow" not in main,
            "is_good_for_photos": "clear" in main or "sun" in description,
        }

    def _get_mock_weather(self) -> dict[str, Any]:
        """Return mock weather data when API is not available."""
        return {
            "temperature": 72,
            "feels_like": 70,
            "humidity": 45,
            "description": "partly cloudy",
            "icon": "02d",
            "main": "Clouds",
            "wind_speed": 8,
            "city": "Your City",
        }

    def _get_mock_forecast(self, days: int) -> list[dict[str, Any]]:
        """Return mock forecast data when API is not available."""
        from datetime import timedelta

        today = datetime.now()
        forecasts = []
        conditions = ["Clear", "Clouds", "Clear", "Rain", "Clear"]

        for i in range(days):
            date = today + timedelta(days=i)
            forecasts.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "day_name": date.strftime("%A"),
                    "temperature": 70 + (i * 2),
                    "temp_min": 65 + (i * 2),
                    "temp_max": 75 + (i * 2),
                    "description": conditions[i % len(conditions)].lower(),
                    "main": conditions[i % len(conditions)],
                    "icon": "01d" if conditions[i % len(conditions)] == "Clear" else "03d",
                }
            )
        return forecasts
