"""Google Trends client using pytrends for search trend analysis."""

import asyncio
from typing import Any
from pytrends.request import TrendReq
from ..core.cache import cached
from ..core.logging import get_logger

logger = get_logger("trends")

# US Metro codes for major cities
US_METRO_CODES = {
    "new york": "US-NY-501",
    "los angeles": "US-CA-803",
    "chicago": "US-IL-602",
    "houston": "US-TX-618",
    "phoenix": "US-AZ-753",
    "philadelphia": "US-PA-504",
    "san antonio": "US-TX-641",
    "san diego": "US-CA-825",
    "dallas": "US-TX-623",
    "san jose": "US-CA-807",
    "austin": "US-TX-635",
    "jacksonville": "US-FL-561",
    "fort worth": "US-TX-623",
    "columbus": "US-OH-535",
    "charlotte": "US-NC-517",
    "san francisco": "US-CA-807",
    "indianapolis": "US-IN-527",
    "seattle": "US-WA-819",
    "denver": "US-CO-751",
    "washington dc": "US-DC-511",
}


class TrendsClient:
    """Client for Google Trends data via pytrends."""

    def __init__(self):
        self._pytrends = TrendReq(hl="en-US", tz=360)

    def _get_metro_code(self, city: str) -> str | None:
        """Get Google Trends metro code for a city."""
        city_lower = city.lower().strip()
        return US_METRO_CODES.get(city_lower)

    @cached(ttl=86400, key_prefix="trends_interest")  # Cache for 24 hours
    async def get_interest_over_time(
        self,
        keywords: list[str],
        city: str | None = None,
        timeframe: str = "today 12-m",
    ) -> dict[str, Any]:
        """
        Get search interest over time for keywords.

        Args:
            keywords: List of search terms (max 5)
            city: City name for geo-filtering
            timeframe: Time range (e.g., 'today 12-m', 'today 3-m', '2023-01-01 2024-01-01')

        Returns:
            Dict with dates and interest values per keyword
        """
        logger.info("Fetching trends interest", keywords=keywords, city=city)

        geo = ""
        if city:
            metro_code = self._get_metro_code(city)
            if metro_code:
                geo = metro_code
            else:
                geo = "US"  # Fallback to US-wide

        try:
            # Run in executor since pytrends is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._fetch_interest(keywords[:5], geo, timeframe),
            )
            return result
        except Exception as e:
            logger.error("Trends API failed", error=str(e))
            return {"error": str(e), "data": []}

    def _fetch_interest(
        self, keywords: list[str], geo: str, timeframe: str
    ) -> dict[str, Any]:
        """Synchronous fetch for interest over time."""
        self._pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
        df = self._pytrends.interest_over_time()

        if df.empty:
            return {"keywords": keywords, "data": [], "geo": geo}

        # Convert to list of dicts
        data = []
        for date, row in df.iterrows():
            entry = {"date": date.strftime("%Y-%m-%d")}
            for kw in keywords:
                if kw in row:
                    entry[kw] = int(row[kw])
            data.append(entry)

        return {
            "keywords": keywords,
            "data": data,
            "geo": geo,
            "timeframe": timeframe,
        }

    @cached(ttl=86400, key_prefix="trends_related")
    async def get_related_queries(
        self, keyword: str, city: str | None = None
    ) -> dict[str, Any]:
        """
        Get related and rising queries for a keyword.

        Args:
            keyword: Search term
            city: City name for geo-filtering

        Returns:
            Dict with top and rising related queries
        """
        logger.info("Fetching related queries", keyword=keyword, city=city)

        geo = ""
        if city:
            metro_code = self._get_metro_code(city)
            geo = metro_code if metro_code else "US"

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._fetch_related(keyword, geo)
            )
            return result
        except Exception as e:
            logger.error("Related queries failed", error=str(e))
            return {"keyword": keyword, "top": [], "rising": []}

    def _fetch_related(self, keyword: str, geo: str) -> dict[str, Any]:
        """Synchronous fetch for related queries."""
        self._pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
        related = self._pytrends.related_queries()

        result = {"keyword": keyword, "geo": geo, "top": [], "rising": []}

        if keyword in related:
            top_df = related[keyword].get("top")
            if top_df is not None and not top_df.empty:
                result["top"] = top_df.head(10).to_dict("records")

            rising_df = related[keyword].get("rising")
            if rising_df is not None and not rising_df.empty:
                result["rising"] = rising_df.head(10).to_dict("records")

        return result

    @cached(ttl=86400, key_prefix="trends_regional")
    async def get_interest_by_region(
        self, keyword: str, resolution: str = "CITY"
    ) -> list[dict[str, Any]]:
        """
        Get search interest by geographic region within the US.

        Args:
            keyword: Search term
            resolution: 'COUNTRY', 'REGION', 'CITY', 'DMA'

        Returns:
            List of regions with interest scores
        """
        logger.info("Fetching regional interest", keyword=keyword, resolution=resolution)

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: self._fetch_regional(keyword, resolution)
            )
            return result
        except Exception as e:
            logger.error("Regional interest failed", error=str(e))
            return []

    def _fetch_regional(self, keyword: str, resolution: str) -> list[dict[str, Any]]:
        """Synchronous fetch for regional interest."""
        self._pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo="US")
        df = self._pytrends.interest_by_region(
            resolution=resolution, inc_low_vol=True, inc_geo_code=True
        )

        if df.empty:
            return []

        results = []
        for geo_name, row in df.iterrows():
            if row[keyword] > 0:
                results.append(
                    {"region": geo_name, "interest": int(row[keyword]), "keyword": keyword}
                )

        return sorted(results, key=lambda x: x["interest"], reverse=True)[:20]


_trends_client: TrendsClient | None = None


def get_trends_client() -> TrendsClient:
    global _trends_client
    if _trends_client is None:
        _trends_client = TrendsClient()
    return _trends_client
