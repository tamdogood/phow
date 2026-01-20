"""GDELT Project API client for news and trend analysis."""

import httpx
from datetime import datetime, timedelta
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ...core.cache import cached
from ...core.logging import get_logger

logger = get_logger("gdelt_client")

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_GEO_API = "https://api.gdeltproject.org/api/v2/geo/geo"


class GDELTClient:
    """Client for GDELT Project API (free, no API key required)."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)  # GDELT can be slow

    async def close(self):
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _request(self, url: str, params: dict) -> dict | list:
        """Make a request to GDELT API."""
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @cached(ttl=14400, key_prefix="gdelt_news")  # 4 hours
    async def search_industry_news(
        self,
        keywords: list[str],
        days_back: int = 30,
        max_records: int = 50,
    ) -> dict[str, Any]:
        """
        Search for industry-related news articles.

        Args:
            keywords: List of search keywords
            days_back: Number of days to search back (max 90)
            max_records: Maximum articles to return

        Returns:
            List of news articles with titles, sources, and dates
        """
        query = " OR ".join(f'"{k}"' for k in keywords)
        start_date = (datetime.now() - timedelta(days=min(days_back, 90))).strftime("%Y%m%d%H%M%S")

        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json",
            "startdatetime": start_date,
            "sort": "datedesc",
        }

        try:
            data = await self._request(GDELT_DOC_API, params)

            articles = data.get("articles", []) if isinstance(data, dict) else []

            return {
                "keywords": keywords,
                "days_searched": days_back,
                "total_found": len(articles),
                "articles": [
                    {
                        "title": a.get("title"),
                        "url": a.get("url"),
                        "source": a.get("domain"),
                        "date": a.get("seendate"),
                        "language": a.get("language"),
                        "source_country": a.get("sourcecountry"),
                    }
                    for a in articles[:max_records]
                ],
            }
        except Exception as e:
            logger.error("GDELT news search failed", error=str(e))
            return {"error": str(e), "keywords": keywords}

    @cached(ttl=14400, key_prefix="gdelt_trends")  # 4 hours
    async def get_trending_topics(
        self,
        theme: str,
        days_back: int = 7,
    ) -> dict[str, Any]:
        """
        Get trending topics related to a theme.

        Args:
            theme: Theme to analyze (e.g., "small business", "retail", "restaurant")
            days_back: Number of days to analyze

        Returns:
            Trending topics and their mention frequencies
        """
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d%H%M%S")

        params = {
            "query": f'"{theme}"',
            "mode": "timelinevol",
            "format": "json",
            "startdatetime": start_date,
            "timelinesmooth": 5,
        }

        try:
            data = await self._request(GDELT_DOC_API, params)

            timeline = data.get("timeline", []) if isinstance(data, dict) else []

            # Calculate trend direction
            if len(timeline) >= 2:
                recent = sum(t.get("value", 0) for t in timeline[:3]) / 3 if len(timeline) >= 3 else timeline[0].get("value", 0)
                older = sum(t.get("value", 0) for t in timeline[-3:]) / 3 if len(timeline) >= 3 else timeline[-1].get("value", 0)
                if older > 0:
                    trend_change = ((recent - older) / older) * 100
                else:
                    trend_change = 0
            else:
                trend_change = 0

            return {
                "theme": theme,
                "days_analyzed": days_back,
                "trend_direction": "increasing" if trend_change > 10 else "decreasing" if trend_change < -10 else "stable",
                "trend_change_percent": round(trend_change, 1),
                "timeline": [
                    {"date": t.get("date"), "volume": t.get("value")}
                    for t in timeline
                ],
                "average_daily_mentions": (
                    sum(t.get("value", 0) for t in timeline) / len(timeline) if timeline else 0
                ),
            }
        except Exception as e:
            logger.error("GDELT trends request failed", error=str(e))
            return {"error": str(e), "theme": theme}

    @cached(ttl=14400, key_prefix="gdelt_sentiment")  # 4 hours
    async def get_sentiment_trends(
        self,
        keyword: str,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """
        Get sentiment trends for a keyword over time.

        Args:
            keyword: Keyword to analyze sentiment for
            days_back: Number of days to analyze

        Returns:
            Sentiment analysis with tone scores
        """
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d%H%M%S")

        params = {
            "query": f'"{keyword}"',
            "mode": "timelinetone",
            "format": "json",
            "startdatetime": start_date,
            "timelinesmooth": 5,
        }

        try:
            data = await self._request(GDELT_DOC_API, params)

            timeline = data.get("timeline", []) if isinstance(data, dict) else []

            # GDELT tone ranges from -100 (very negative) to +100 (very positive)
            tones = [t.get("value", 0) for t in timeline if t.get("value") is not None]
            avg_tone = sum(tones) / len(tones) if tones else 0

            return {
                "keyword": keyword,
                "days_analyzed": days_back,
                "average_tone": round(avg_tone, 2),
                "sentiment": (
                    "positive" if avg_tone > 2 else "negative" if avg_tone < -2 else "neutral"
                ),
                "tone_timeline": [
                    {"date": t.get("date"), "tone": t.get("value")}
                    for t in timeline
                ],
                "interpretation": self._interpret_tone(avg_tone),
            }
        except Exception as e:
            logger.error("GDELT sentiment request failed", error=str(e))
            return {"error": str(e), "keyword": keyword}

    def _interpret_tone(self, tone: float) -> str:
        """Interpret GDELT tone score."""
        if tone > 5:
            return "Very positive media coverage - favorable public perception"
        elif tone > 2:
            return "Slightly positive media coverage"
        elif tone > -2:
            return "Neutral media coverage"
        elif tone > -5:
            return "Slightly negative media coverage"
        else:
            return "Negative media coverage - potential reputation concerns"


# Singleton instance
_gdelt_client: GDELTClient | None = None


def get_gdelt_client() -> GDELTClient:
    global _gdelt_client
    if _gdelt_client is None:
        _gdelt_client = GDELTClient()
    return _gdelt_client
