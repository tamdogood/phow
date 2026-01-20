"""Federal Reserve Economic Data (FRED) API client for economic indicators."""

import httpx
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ...core.cache import cached
from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.rate_limiter import get_rate_limiter

logger = get_logger("fred_client")

FRED_API_BASE = "https://api.stlouisfed.org/fred"

# Key economic series IDs
ECONOMIC_SERIES = {
    "gdp": "GDP",
    "unemployment": "UNRATE",
    "cpi": "CPIAUCSL",
    "consumer_confidence": "UMCSENT",
    "retail_sales": "RSXFS",
    "personal_income": "PI",
    "housing_starts": "HOUST",
    "industrial_production": "INDPRO",
}


class FREDClient:
    """Client for Federal Reserve Economic Data (FRED) API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.fred_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = get_rate_limiter()

    async def close(self):
        await self.client.aclose()

    async def _check_rate_limit(self) -> bool:
        return await self.rate_limiter.acquire("fred")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _request(self, endpoint: str, params: dict) -> dict:
        """Make a request to FRED API."""
        if not await self._check_rate_limit():
            logger.warning("FRED rate limit exceeded")
            return {"error": "Rate limit exceeded"}

        params["api_key"] = self.api_key
        params["file_type"] = "json"

        response = await self.client.get(f"{FRED_API_BASE}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    @cached(ttl=86400, key_prefix="fred_series")  # 24 hours
    async def get_series(
        self,
        series_id: str,
        observation_start: str | None = None,
        observation_end: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get time series data for a FRED series.

        Args:
            series_id: FRED series ID (e.g., "GDP", "UNRATE")
            observation_start: Start date (YYYY-MM-DD)
            observation_end: End date (YYYY-MM-DD)
            limit: Maximum observations to return

        Returns:
            Series data with observations
        """
        if not self.api_key:
            return {"error": "FRED API key not configured"}

        params = {
            "series_id": series_id,
            "sort_order": "desc",
            "limit": limit,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        try:
            # Get series info
            info_data = await self._request("series", {"series_id": series_id})
            series_info = info_data.get("seriess", [{}])[0]

            # Get observations
            obs_data = await self._request("series/observations", params)
            observations = obs_data.get("observations", [])

            return {
                "series_id": series_id,
                "title": series_info.get("title"),
                "units": series_info.get("units"),
                "frequency": series_info.get("frequency"),
                "seasonal_adjustment": series_info.get("seasonal_adjustment"),
                "last_updated": series_info.get("last_updated"),
                "observations": [
                    {
                        "date": o.get("date"),
                        "value": float(o.get("value")) if o.get("value") != "." else None,
                    }
                    for o in observations
                ],
                "latest_value": (
                    float(observations[0]["value"])
                    if observations and observations[0].get("value") != "."
                    else None
                ),
                "latest_date": observations[0].get("date") if observations else None,
            }
        except Exception as e:
            logger.error("FRED series request failed", error=str(e), series_id=series_id)
            return {"error": str(e)}

    @cached(ttl=86400, key_prefix="fred_regional")  # 24 hours
    async def get_regional_data(
        self, series_id: str, region_type: str = "state"
    ) -> dict[str, Any]:
        """
        Get regional data for a series (state-level breakdown).

        Args:
            series_id: Base series ID
            region_type: Type of region ("state", "msa")

        Returns:
            Regional breakdown of the series
        """
        if not self.api_key:
            return {"error": "FRED API key not configured"}

        # State unemployment series follow pattern: {STATE}UR (e.g., TXUR for Texas)
        state_codes = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        ]

        regional_data = {}

        if series_id == "UNRATE" and region_type == "state":
            # Fetch state unemployment rates
            for state in state_codes[:10]:  # Limit to avoid rate limits
                state_series = f"{state}UR"
                try:
                    data = await self.get_series(state_series, limit=1)
                    if "error" not in data and data.get("latest_value"):
                        regional_data[state] = data["latest_value"]
                except Exception:
                    continue

        return {
            "base_series": series_id,
            "region_type": region_type,
            "regional_values": regional_data,
        }

    @cached(ttl=86400, key_prefix="fred_indicators")  # 24 hours
    async def get_economic_indicators(self) -> dict[str, Any]:
        """
        Get current values for key economic indicators.

        Returns:
            Dictionary of economic indicators with latest values
        """
        if not self.api_key:
            return {"error": "FRED API key not configured"}

        indicators = {}

        for name, series_id in ECONOMIC_SERIES.items():
            try:
                data = await self.get_series(series_id, limit=1)
                if "error" not in data:
                    indicators[name] = {
                        "series_id": series_id,
                        "title": data.get("title"),
                        "value": data.get("latest_value"),
                        "date": data.get("latest_date"),
                        "units": data.get("units"),
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {name}", error=str(e))
                indicators[name] = {"error": str(e)}

        # Add interpretations
        indicators["_interpretation"] = self._interpret_indicators(indicators)

        return indicators

    def _interpret_indicators(self, indicators: dict) -> dict:
        """Generate human-readable interpretations of economic indicators."""
        interpretations = {}

        # Unemployment interpretation
        if "unemployment" in indicators and indicators["unemployment"].get("value"):
            rate = indicators["unemployment"]["value"]
            if rate < 4:
                interpretations["unemployment"] = "Very tight labor market - hiring may be challenging"
            elif rate < 5:
                interpretations["unemployment"] = "Healthy labor market - moderate hiring conditions"
            elif rate < 7:
                interpretations["unemployment"] = "Elevated unemployment - larger talent pool available"
            else:
                interpretations["unemployment"] = "High unemployment - economic stress, but hiring easier"

        # Consumer confidence interpretation
        if "consumer_confidence" in indicators and indicators["consumer_confidence"].get("value"):
            conf = indicators["consumer_confidence"]["value"]
            if conf > 100:
                interpretations["consumer_confidence"] = "High consumer optimism - favorable for discretionary spending"
            elif conf > 80:
                interpretations["consumer_confidence"] = "Moderate consumer confidence - stable spending expected"
            else:
                interpretations["consumer_confidence"] = "Low consumer confidence - cautious spending environment"

        # CPI interpretation
        if "cpi" in indicators and indicators["cpi"].get("value"):
            interpretations["cpi"] = "Monitor for pricing strategy adjustments"

        return interpretations


# Singleton instance
_fred_client: FREDClient | None = None


def get_fred_client() -> FREDClient:
    global _fred_client
    if _fred_client is None:
        _fred_client = FREDClient()
    return _fred_client
