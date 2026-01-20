"""Bureau of Labor Statistics (BLS) API client for employment and wage data."""

import httpx
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ...core.cache import cached
from ...core.config import get_settings
from ...core.logging import get_logger
from ...core.rate_limiter import get_rate_limiter

logger = get_logger("bls_client")

BLS_API_BASE = "https://api.bls.gov/publicAPI/v2"


class BLSClient:
    """Client for Bureau of Labor Statistics API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.bls_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = get_rate_limiter()

    async def close(self):
        await self.client.aclose()

    async def _check_rate_limit(self) -> bool:
        return await self.rate_limiter.acquire("bls")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _request(self, series_ids: list[str], start_year: int, end_year: int) -> dict:
        """Make a request to BLS API."""
        if not await self._check_rate_limit():
            logger.warning("BLS rate limit exceeded")
            return {"error": "Rate limit exceeded"}

        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if self.api_key:
            payload["registrationkey"] = self.api_key

        response = await self.client.post(f"{BLS_API_BASE}/timeseries/data/", json=payload)
        response.raise_for_status()
        return response.json()

    @cached(ttl=604800, key_prefix="bls_employment")  # 7 days
    async def get_employment_by_industry(
        self, naics_code: str, area_code: str = "0000000"
    ) -> dict[str, Any]:
        """
        Get employment data by industry (NAICS code).

        Args:
            naics_code: 2-6 digit NAICS industry code
            area_code: BLS area code (default: national)

        Returns:
            Employment data including total employment and trends
        """
        # QCEW series format: ENU{area}{size}{ownership}{naics}
        # Using size=0 (all), ownership=0 (all)
        series_id = f"ENU{area_code}00{naics_code.zfill(6)[:6]}"

        import datetime
        current_year = datetime.datetime.now().year
        start_year = current_year - 5

        try:
            data = await self._request([series_id], start_year, current_year)

            if data.get("status") != "REQUEST_SUCCEEDED":
                return {"error": data.get("message", ["Unknown error"])}

            results = data.get("Results", {}).get("series", [])
            if not results:
                return {"error": "No data found for this industry/area"}

            series_data = results[0].get("data", [])

            return {
                "naics_code": naics_code,
                "area_code": area_code,
                "series_id": series_id,
                "data_points": [
                    {
                        "year": d.get("year"),
                        "period": d.get("period"),
                        "value": float(d.get("value", 0).replace(",", "")),
                        "footnotes": d.get("footnotes", []),
                    }
                    for d in series_data
                ],
                "latest_value": float(series_data[0]["value"].replace(",", "")) if series_data else None,
            }
        except Exception as e:
            logger.error("BLS employment request failed", error=str(e))
            return {"error": str(e)}

    @cached(ttl=604800, key_prefix="bls_wages")  # 7 days
    async def get_wage_data(
        self, occupation_code: str, area_code: str = "0000000"
    ) -> dict[str, Any]:
        """
        Get wage data by occupation code.

        Args:
            occupation_code: SOC occupation code (e.g., "00-0000" for all occupations)
            area_code: BLS area code (default: national)

        Returns:
            Wage statistics including median, mean, percentiles
        """
        # OES series format: OEUS{area}{industry}{occupation}{datatype}
        # Using industry=000000 (all), datatype varies
        occ_clean = occupation_code.replace("-", "")

        # Fetch multiple data types: annual mean wage (04), hourly mean (03)
        series_ids = [
            f"OEUM{area_code}000000{occ_clean}04",  # Annual mean wage
            f"OEUM{area_code}000000{occ_clean}03",  # Hourly mean wage
        ]

        import datetime
        current_year = datetime.datetime.now().year

        try:
            data = await self._request(series_ids, current_year - 2, current_year)

            if data.get("status") != "REQUEST_SUCCEEDED":
                return {"error": data.get("message", ["Unknown error"])}

            results = {}
            for series in data.get("Results", {}).get("series", []):
                series_id = series.get("seriesID", "")
                series_data = series.get("data", [])
                if series_data:
                    latest = series_data[0]
                    if series_id.endswith("04"):
                        results["annual_mean_wage"] = float(latest["value"].replace(",", ""))
                    elif series_id.endswith("03"):
                        results["hourly_mean_wage"] = float(latest["value"].replace(",", ""))

            return {
                "occupation_code": occupation_code,
                "area_code": area_code,
                **results,
            }
        except Exception as e:
            logger.error("BLS wage request failed", error=str(e))
            return {"error": str(e)}

    @cached(ttl=604800, key_prefix="bls_trends")  # 7 days
    async def get_industry_employment_trends(self, naics_code: str) -> dict[str, Any]:
        """
        Get employment trend data for an industry.

        Args:
            naics_code: NAICS industry code

        Returns:
            Historical employment data with growth calculations
        """
        # CES series for employment trends (national only)
        # Format: CES{supersector}{industry}01
        naics_2digit = naics_code[:2]

        # Map NAICS to CES supersector codes
        naics_to_ces = {
            "11": "1000000001",  # Natural resources
            "21": "1000000001",  # Mining
            "23": "2000000001",  # Construction
            "31": "3000000001",  # Manufacturing
            "32": "3000000001",
            "33": "3000000001",
            "42": "4000000001",  # Wholesale trade
            "44": "4100000001",  # Retail trade
            "45": "4100000001",
            "48": "4300000001",  # Transportation
            "49": "4300000001",
            "51": "5000000001",  # Information
            "52": "5500000001",  # Financial
            "53": "5500000001",
            "54": "6000000001",  # Professional services
            "55": "6000000001",
            "56": "6000000001",
            "61": "6500000001",  # Education
            "62": "6500000001",  # Healthcare
            "71": "7000000001",  # Leisure/hospitality
            "72": "7000000001",
            "81": "8000000001",  # Other services
        }

        ces_code = naics_to_ces.get(naics_2digit, "0000000001")
        series_id = f"CES{ces_code}"

        import datetime
        current_year = datetime.datetime.now().year
        start_year = current_year - 10

        try:
            data = await self._request([series_id], start_year, current_year)

            if data.get("status") != "REQUEST_SUCCEEDED":
                return {"error": data.get("message", ["Unknown error"])}

            results = data.get("Results", {}).get("series", [])
            if not results:
                return {"error": "No trend data found"}

            series_data = results[0].get("data", [])
            values = [
                {
                    "year": d.get("year"),
                    "period": d.get("period"),
                    "value": float(d.get("value", 0).replace(",", "")),
                }
                for d in series_data
                if d.get("period") == "M13"  # Annual average
            ]

            # Calculate growth rate
            if len(values) >= 2:
                latest = values[0]["value"]
                oldest = values[-1]["value"]
                years = int(values[0]["year"]) - int(values[-1]["year"])
                if years > 0 and oldest > 0:
                    cagr = ((latest / oldest) ** (1 / years) - 1) * 100
                else:
                    cagr = 0
            else:
                cagr = 0

            return {
                "naics_code": naics_code,
                "series_id": series_id,
                "annual_data": values,
                "cagr_percent": round(cagr, 2),
                "latest_employment": values[0]["value"] if values else None,
            }
        except Exception as e:
            logger.error("BLS trends request failed", error=str(e))
            return {"error": str(e)}


# Singleton instance
_bls_client: BLSClient | None = None


def get_bls_client() -> BLSClient:
    global _bls_client
    if _bls_client is None:
        _bls_client = BLSClient()
    return _bls_client
