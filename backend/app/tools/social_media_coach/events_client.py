"""Client for local events and holidays data."""

import httpx
from typing import Any
from datetime import datetime, timedelta
from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.cache import cached

logger = get_logger("events_client")


# Common US holidays and observances relevant to businesses
HOLIDAYS_2024_2025 = [
    {"date": "2024-01-01", "name": "New Year's Day", "type": "holiday"},
    {"date": "2024-01-15", "name": "Martin Luther King Jr. Day", "type": "holiday"},
    {"date": "2024-02-14", "name": "Valentine's Day", "type": "observance"},
    {"date": "2024-02-19", "name": "Presidents' Day", "type": "holiday"},
    {"date": "2024-03-17", "name": "St. Patrick's Day", "type": "observance"},
    {"date": "2024-03-31", "name": "Easter Sunday", "type": "holiday"},
    {"date": "2024-04-22", "name": "Earth Day", "type": "observance"},
    {"date": "2024-05-05", "name": "Cinco de Mayo", "type": "observance"},
    {"date": "2024-05-12", "name": "Mother's Day", "type": "observance"},
    {"date": "2024-05-27", "name": "Memorial Day", "type": "holiday"},
    {"date": "2024-06-16", "name": "Father's Day", "type": "observance"},
    {"date": "2024-06-19", "name": "Juneteenth", "type": "holiday"},
    {"date": "2024-07-04", "name": "Independence Day", "type": "holiday"},
    {"date": "2024-09-02", "name": "Labor Day", "type": "holiday"},
    {"date": "2024-10-14", "name": "Columbus Day", "type": "holiday"},
    {"date": "2024-10-31", "name": "Halloween", "type": "observance"},
    {"date": "2024-11-11", "name": "Veterans Day", "type": "holiday"},
    {"date": "2024-11-28", "name": "Thanksgiving", "type": "holiday"},
    {"date": "2024-11-29", "name": "Black Friday", "type": "observance"},
    {"date": "2024-12-02", "name": "Cyber Monday", "type": "observance"},
    {"date": "2024-12-24", "name": "Christmas Eve", "type": "observance"},
    {"date": "2024-12-25", "name": "Christmas Day", "type": "holiday"},
    {"date": "2024-12-31", "name": "New Year's Eve", "type": "observance"},
    {"date": "2025-01-01", "name": "New Year's Day", "type": "holiday"},
    {"date": "2025-01-20", "name": "Martin Luther King Jr. Day", "type": "holiday"},
    {"date": "2025-02-14", "name": "Valentine's Day", "type": "observance"},
    {"date": "2025-02-17", "name": "Presidents' Day", "type": "holiday"},
    {"date": "2025-03-17", "name": "St. Patrick's Day", "type": "observance"},
    {"date": "2025-04-20", "name": "Easter Sunday", "type": "holiday"},
    {"date": "2025-04-22", "name": "Earth Day", "type": "observance"},
    {"date": "2025-05-05", "name": "Cinco de Mayo", "type": "observance"},
    {"date": "2025-05-11", "name": "Mother's Day", "type": "observance"},
    {"date": "2025-05-26", "name": "Memorial Day", "type": "holiday"},
    {"date": "2025-06-15", "name": "Father's Day", "type": "observance"},
    {"date": "2025-06-19", "name": "Juneteenth", "type": "holiday"},
    {"date": "2025-07-04", "name": "Independence Day", "type": "holiday"},
    {"date": "2025-09-01", "name": "Labor Day", "type": "holiday"},
    {"date": "2025-10-13", "name": "Columbus Day", "type": "holiday"},
    {"date": "2025-10-31", "name": "Halloween", "type": "observance"},
    {"date": "2025-11-11", "name": "Veterans Day", "type": "holiday"},
    {"date": "2025-11-27", "name": "Thanksgiving", "type": "holiday"},
    {"date": "2025-11-28", "name": "Black Friday", "type": "observance"},
    {"date": "2025-12-01", "name": "Cyber Monday", "type": "observance"},
    {"date": "2025-12-24", "name": "Christmas Eve", "type": "observance"},
    {"date": "2025-12-25", "name": "Christmas Day", "type": "holiday"},
    {"date": "2025-12-31", "name": "New Year's Eve", "type": "observance"},
]

# Daily and weekly content themes
DAILY_THEMES = {
    0: ["Motivation Monday", "New week, new goals", "Monday mood"],
    1: ["Tip Tuesday", "Tuesday thoughts", "Transformation Tuesday"],
    2: ["Wednesday Wisdom", "Hump day", "Midweek motivation"],
    3: ["Throwback Thursday", "#TBT", "Thursday thoughts"],
    4: ["Feel-good Friday", "TGIF", "Friday favorites"],
    5: ["Small Business Saturday", "Weekend vibes", "Saturday specials"],
    6: ["Self-care Sunday", "Sunday funday", "Week ahead preview"],
}


class EventsClient:
    """Client for local events and holiday data."""

    _client: httpx.AsyncClient | None = None

    def __init__(self):
        settings = get_settings()
        self.eventbrite_key = getattr(settings, "eventbrite_api_key", None)

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create a reusable httpx client."""
        if EventsClient._client is None:
            EventsClient._client = httpx.AsyncClient()
        return EventsClient._client

    def get_upcoming_holidays(self, days_ahead: int = 14) -> list[dict[str, Any]]:
        """Get holidays and observances in the next N days."""
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)

        upcoming = []
        for holiday in HOLIDAYS_2024_2025:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d").date()
            if today <= holiday_date <= end_date:
                days_until = (holiday_date - today).days
                upcoming.append({
                    **holiday,
                    "days_until": days_until,
                    "is_today": days_until == 0,
                    "is_tomorrow": days_until == 1,
                    "is_this_week": days_until <= 7,
                })

        return sorted(upcoming, key=lambda x: x["days_until"])

    def get_daily_themes(self) -> dict[str, Any]:
        """Get content themes for today."""
        today = datetime.now()
        day_of_week = today.weekday()
        themes = DAILY_THEMES.get(day_of_week, [])

        return {
            "day_name": today.strftime("%A"),
            "date": today.strftime("%B %d, %Y"),
            "themes": themes,
            "hashtag_suggestions": [f"#{theme.replace(' ', '')}" for theme in themes if len(theme) < 25],
        }

    @cached(ttl=3600, key_prefix="local_events")
    async def get_local_events(
        self, lat: float, lng: float, radius_miles: int = 10, days_ahead: int = 7
    ) -> list[dict[str, Any]]:
        """Get local events near a location."""
        # For now, return mock events since Eventbrite API requires OAuth
        # In production, this would call the Eventbrite API
        logger.info("Getting local events", lat=lat, lng=lng, radius=radius_miles)

        if not self.eventbrite_key:
            logger.warning("Eventbrite API key not configured, using mock events")
            return self._get_mock_events(days_ahead)

        # TODO: Implement actual Eventbrite API call when key is available
        # The Eventbrite API requires OAuth2, so we'd need to implement that flow
        return self._get_mock_events(days_ahead)

    def _get_mock_events(self, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Return mock local events for demonstration."""
        today = datetime.now()
        events = []

        # Generate some realistic mock events
        mock_event_templates = [
            {"name": "Farmers Market", "category": "food", "recurring": "weekly"},
            {"name": "Live Music Night", "category": "music", "recurring": "weekly"},
            {"name": "Community Yoga", "category": "fitness", "recurring": "weekly"},
            {"name": "Art Walk", "category": "arts", "recurring": "monthly"},
            {"name": "Food Truck Rally", "category": "food", "recurring": "monthly"},
            {"name": "Small Business Networking", "category": "business", "recurring": "monthly"},
        ]

        for i, template in enumerate(mock_event_templates):
            if i < days_ahead:
                event_date = today + timedelta(days=i + 1)
                events.append({
                    "name": template["name"],
                    "date": event_date.strftime("%Y-%m-%d"),
                    "day_name": event_date.strftime("%A"),
                    "category": template["category"],
                    "distance": f"{(i + 1) * 0.5:.1f} miles away",
                    "relevance": "May increase foot traffic" if template["category"] in ["food", "arts"] else "Networking opportunity",
                })

        return events

    def get_content_opportunities(
        self,
        business_type: str,
        holidays: list[dict],
        events: list[dict],
        daily_themes: dict,
    ) -> list[dict[str, Any]]:
        """Analyze holidays/events and suggest content opportunities."""
        opportunities = []

        # Today's themes
        for theme in daily_themes.get("themes", [])[:2]:
            opportunities.append({
                "type": "daily_theme",
                "title": theme,
                "urgency": "today",
                "suggestion": f"Create a post around '{theme}' - it's a popular hashtag today",
            })

        # Upcoming holidays
        for holiday in holidays[:3]:
            if holiday.get("is_today"):
                opportunities.append({
                    "type": "holiday",
                    "title": holiday["name"],
                    "urgency": "now",
                    "suggestion": f"Post about {holiday['name']}! Share how you're celebrating or any special offers.",
                })
            elif holiday.get("is_tomorrow"):
                opportunities.append({
                    "type": "holiday",
                    "title": holiday["name"],
                    "urgency": "tomorrow",
                    "suggestion": f"{holiday['name']} is tomorrow - perfect time for a teaser or reminder post.",
                })
            elif holiday.get("is_this_week"):
                opportunities.append({
                    "type": "holiday",
                    "title": holiday["name"],
                    "urgency": "this_week",
                    "suggestion": f"{holiday['name']} is in {holiday['days_until']} days - start building anticipation!",
                })

        # Local events
        for event in events[:2]:
            opportunities.append({
                "type": "local_event",
                "title": event["name"],
                "urgency": "upcoming",
                "suggestion": f"{event['name']} is happening {event['day_name']}. {event.get('relevance', 'Great content opportunity!')}",
            })

        return opportunities
