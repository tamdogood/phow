"""Unified data fetcher that orchestrates data collection from all sources."""

import asyncio
from datetime import datetime
from typing import Any
from ...core.logging import get_logger
from .bls_client import get_bls_client
from .fred_client import get_fred_client
from .gdelt_client import get_gdelt_client
from .naics_service import get_naics_service
from ..location_scout.google_maps import GoogleMapsClient
from ..market_validator.census_client import get_census_client

logger = get_logger("data_fetcher")

# Default timeout for each data source (in seconds)
DEFAULT_TIMEOUT = 15


class DataFetcher:
    """Orchestrates data fetching from multiple sources with parallel execution and graceful degradation."""

    def __init__(self):
        self.bls = get_bls_client()
        self.fred = get_fred_client()
        self.gdelt = get_gdelt_client()
        self.naics = get_naics_service()
        self.census = get_census_client()
        self.maps = GoogleMapsClient()

    async def fetch_market_data(
        self,
        location: str,
        business_type: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Fetch comprehensive market data for a location and business type.

        Args:
            location: Address or location string
            business_type: Type of business (e.g., "coffee shop")
            timeout: Timeout per data source in seconds

        Returns:
            Aggregated market data from all sources with freshness metadata
        """
        start_time = datetime.now()
        results = {
            "location": location,
            "business_type": business_type,
            "fetched_at": start_time.isoformat(),
            "sources_available": [],
            "sources_failed": [],
            "data": {},
        }

        # Get NAICS codes for the business type
        naics_codes = self.naics.map_business_type(business_type)
        primary_naics = naics_codes[0] if naics_codes else None
        results["naics_codes"] = naics_codes
        results["primary_naics"] = primary_naics

        # Define all fetch tasks
        tasks = {
            "geocoding": self._fetch_with_timeout(
                self._fetch_geocoding(location), timeout, "geocoding"
            ),
            "demographics": self._fetch_with_timeout(
                self._fetch_demographics(location), timeout, "demographics"
            ),
            "economic_indicators": self._fetch_with_timeout(
                self._fetch_economic_indicators(), timeout, "economic_indicators"
            ),
            "industry_trends": self._fetch_with_timeout(
                self._fetch_industry_trends(business_type), timeout, "industry_trends"
            ),
        }

        # Add BLS data if we have a NAICS code
        if primary_naics:
            tasks["employment_data"] = self._fetch_with_timeout(
                self._fetch_employment_data(primary_naics), timeout, "employment_data"
            )

        # Execute all tasks in parallel
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Process results
        for (name, _), result in zip(tasks.items(), task_results):
            if isinstance(result, Exception):
                logger.warning(f"Data source failed: {name}", error=str(result))
                results["sources_failed"].append(name)
            elif result and "error" not in result:
                results["data"][name] = result
                results["sources_available"].append(name)
            else:
                results["sources_failed"].append(name)
                if result and "error" in result:
                    logger.warning(f"Data source returned error: {name}", error=result["error"])

        # Add fetch duration
        results["fetch_duration_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)

        return results

    async def fetch_industry_data(
        self,
        naics_code: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """
        Fetch industry-specific data for a NAICS code.

        Args:
            naics_code: NAICS industry code
            timeout: Timeout per data source in seconds

        Returns:
            Industry data from BLS, FRED, and other sources
        """
        start_time = datetime.now()
        results = {
            "naics_code": naics_code,
            "fetched_at": start_time.isoformat(),
            "sources_available": [],
            "sources_failed": [],
            "data": {},
        }

        # Get industry info from NAICS service
        industry_info = self.naics.lookup_code(naics_code)
        if industry_info:
            results["industry_info"] = industry_info
            results["sources_available"].append("naics_lookup")

        # Define fetch tasks
        tasks = {
            "employment": self._fetch_with_timeout(
                self._fetch_employment_data(naics_code), timeout, "employment"
            ),
            "trends": self._fetch_with_timeout(
                self.bls.get_industry_employment_trends(naics_code), timeout, "trends"
            ),
            "economic_indicators": self._fetch_with_timeout(
                self._fetch_economic_indicators(), timeout, "economic_indicators"
            ),
        }

        # Execute in parallel
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for (name, _), result in zip(tasks.items(), task_results):
            if isinstance(result, Exception):
                results["sources_failed"].append(name)
            elif result and "error" not in result:
                results["data"][name] = result
                results["sources_available"].append(name)
            else:
                results["sources_failed"].append(name)

        results["fetch_duration_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
        return results

    async def _fetch_with_timeout(
        self,
        coro,
        timeout: float,
        source_name: str,
    ) -> Any:
        """Execute a coroutine with timeout, returning None on timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {source_name}")
            return {"error": f"Timeout after {timeout}s"}
        except Exception as e:
            logger.error(f"Error fetching {source_name}", error=str(e))
            return {"error": str(e)}

    async def _fetch_geocoding(self, location: str) -> dict[str, Any]:
        """Fetch geocoding data for a location."""
        result = await self.maps.geocode(location)
        if result:
            return {
                "lat": result.get("lat"),
                "lng": result.get("lng"),
                "formatted_address": result.get("formatted_address"),
                "place_id": result.get("place_id"),
            }
        return {"error": "Geocoding failed"}

    async def _fetch_demographics(self, location: str) -> dict[str, Any]:
        """Fetch demographic data for a location."""
        # First geocode to get coordinates
        geo = await self.maps.geocode(location)
        if not geo:
            return {"error": "Could not geocode location"}

        lat, lng = geo["lat"], geo["lng"]

        # Get Census geography
        geography = await self.census.get_geography_for_coordinates(lat, lng)
        if not geography:
            return {"error": "Could not find Census geography"}

        # Get demographics
        demographics = await self.census.get_demographics(
            state_fips=geography["state_fips"],
            county_fips=geography["county_fips"],
            tract_fips=geography.get("tract_fips"),
        )

        return {
            "geography": {
                "county": geography.get("county_name"),
                "state": geography.get("state_name"),
            },
            "demographics": demographics,
            "freshness": "Census ACS 2022 data",
        }

    async def _fetch_economic_indicators(self) -> dict[str, Any]:
        """Fetch current economic indicators from FRED."""
        return await self.fred.get_economic_indicators()

    async def _fetch_industry_trends(self, business_type: str) -> dict[str, Any]:
        """Fetch industry news and trends from GDELT."""
        news = await self.gdelt.search_industry_news([business_type], days_back=30, max_records=10)
        trends = await self.gdelt.get_trending_topics(business_type, days_back=7)
        sentiment = await self.gdelt.get_sentiment_trends(business_type, days_back=30)

        return {
            "news_summary": {
                "total_articles": news.get("total_found", 0),
                "recent_headlines": [a.get("title") for a in news.get("articles", [])[:5]],
            },
            "trend_direction": trends.get("trend_direction"),
            "trend_change_percent": trends.get("trend_change_percent"),
            "media_sentiment": sentiment.get("sentiment"),
            "average_tone": sentiment.get("average_tone"),
        }

    async def _fetch_employment_data(self, naics_code: str) -> dict[str, Any]:
        """Fetch employment data from BLS."""
        employment = await self.bls.get_employment_by_industry(naics_code)
        trends = await self.bls.get_industry_employment_trends(naics_code)

        return {
            "employment": employment,
            "trends": {
                "cagr_percent": trends.get("cagr_percent"),
                "latest_employment": trends.get("latest_employment"),
            },
        }


# Singleton instance
_data_fetcher: DataFetcher | None = None


def get_data_fetcher() -> DataFetcher:
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
