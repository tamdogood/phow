"""Census Bureau API client for demographic data."""

import httpx
from typing import Any
from ...core.logging import get_logger
from ...core.cache import cached

logger = get_logger("census_client")

# Census API base URL (free, no API key required for basic access)
CENSUS_API_BASE = "https://api.census.gov/data"


class CensusClient:
    """Client for US Census Bureau API."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @cached(ttl=86400, key_prefix="census_geo")  # Cache for 24 hours
    async def get_geography_for_coordinates(
        self, lat: float, lng: float
    ) -> dict[str, Any] | None:
        """
        Get Census geography (state, county, tract) for coordinates.
        Uses FCC API to convert coordinates to FIPS codes.
        """
        try:
            # Use FCC Area API to get Census block info
            url = "https://geo.fcc.gov/api/census/area"
            params = {
                "lat": lat,
                "lon": lng,
                "format": "json",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                result = data["results"][0]
                block_fips = result.get("block_fips", "")
                if len(block_fips) >= 11:
                    return {
                        "state_fips": block_fips[:2],
                        "county_fips": block_fips[2:5],
                        "tract_fips": block_fips[5:11],
                        "block_fips": block_fips,
                        "county_name": result.get("county_name", ""),
                        "state_name": result.get("state_name", ""),
                    }
            return None
        except Exception as e:
            logger.error("Failed to get geography for coordinates", error=str(e))
            return None

    @cached(ttl=86400, key_prefix="census_demo")  # Cache for 24 hours
    async def get_demographics(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any]:
        """
        Get demographic data for a Census geography.
        Uses ACS 5-Year estimates.
        """
        demographics = {
            "population": {},
            "income": {},
            "age_distribution": {},
            "education": {},
            "housing": {},
        }

        try:
            # ACS 5-Year data (2022)
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Key variables:
            # B01001_001E - Total population
            # B19013_001E - Median household income
            # B01002_001E - Median age
            # B15003_022E - Bachelor's degree
            # B15003_023E - Master's degree
            # B15003_025E - Doctorate degree
            # B25001_001E - Total housing units
            # B25002_002E - Occupied housing units
            # B25077_001E - Median home value

            variables = [
                "B01001_001E",  # Total population
                "B19013_001E",  # Median household income
                "B01002_001E",  # Median age
                "B25001_001E",  # Total housing units
                "B25002_002E",  # Occupied housing units
                "B25077_001E",  # Median home value
            ]

            # Build the geographic filter
            if tract_fips:
                geo_filter = f"for=tract:{tract_fips}&in=state:{state_fips}&in=county:{county_fips}"
            else:
                geo_filter = f"for=county:{county_fips}&in=state:{state_fips}"

            url = f"{CENSUS_API_BASE}/{dataset}?get={','.join(variables)}&{geo_filter}"

            logger.debug("Fetching Census data", url=url)
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if len(data) >= 2:
                headers = data[0]
                values = data[1]

                # Map values to our structure
                value_map = dict(zip(headers, values))

                demographics["population"] = {
                    "total": self._safe_int(value_map.get("B01001_001E")),
                }
                demographics["income"] = {
                    "median_household": self._safe_int(value_map.get("B19013_001E")),
                }
                demographics["age_distribution"] = {
                    "median_age": self._safe_float(value_map.get("B01002_001E")),
                }
                demographics["housing"] = {
                    "total_units": self._safe_int(value_map.get("B25001_001E")),
                    "occupied_units": self._safe_int(value_map.get("B25002_002E")),
                    "median_home_value": self._safe_int(value_map.get("B25077_001E")),
                }

            # Get age breakdown separately
            age_data = await self._get_age_breakdown(state_fips, county_fips, tract_fips)
            if age_data:
                demographics["age_distribution"].update(age_data)

            # Get education data
            education_data = await self._get_education_data(state_fips, county_fips, tract_fips)
            if education_data:
                demographics["education"] = education_data

            return demographics

        except Exception as e:
            logger.error("Failed to get demographics", error=str(e))
            return demographics

    async def _get_age_breakdown(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get detailed age breakdown."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Age group variables (male + female combined in B01001)
            # Under 18, 18-34, 35-54, 55+
            variables = [
                "B01001_001E",  # Total
                "B01001_003E", "B01001_004E", "B01001_005E", "B01001_006E",  # Male under 18
                "B01001_027E", "B01001_028E", "B01001_029E", "B01001_030E",  # Female under 18
                "B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E", "B01001_011E", "B01001_012E",  # Male 18-34
                "B01001_031E", "B01001_032E", "B01001_033E", "B01001_034E", "B01001_035E", "B01001_036E",  # Female 18-34
            ]

            if tract_fips:
                geo_filter = f"for=tract:{tract_fips}&in=state:{state_fips}&in=county:{county_fips}"
            else:
                geo_filter = f"for=county:{county_fips}&in=state:{state_fips}"

            url = f"{CENSUS_API_BASE}/{dataset}?get={','.join(variables)}&{geo_filter}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if len(data) >= 2:
                headers = data[0]
                values = data[1]
                value_map = dict(zip(headers, values))

                total = self._safe_int(value_map.get("B01001_001E")) or 1

                # Calculate under 18
                under_18_vars = ["B01001_003E", "B01001_004E", "B01001_005E", "B01001_006E",
                                 "B01001_027E", "B01001_028E", "B01001_029E", "B01001_030E"]
                under_18 = sum(self._safe_int(value_map.get(v)) for v in under_18_vars)

                # Calculate 18-34
                age_18_34_vars = ["B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E",
                                  "B01001_011E", "B01001_012E", "B01001_031E", "B01001_032E",
                                  "B01001_033E", "B01001_034E", "B01001_035E", "B01001_036E"]
                age_18_34 = sum(self._safe_int(value_map.get(v)) for v in age_18_34_vars)

                return {
                    "under_18_percent": round((under_18 / total) * 100, 1),
                    "age_18_34_percent": round((age_18_34 / total) * 100, 1),
                    "age_35_plus_percent": round(((total - under_18 - age_18_34) / total) * 100, 1),
                }

            return None
        except Exception as e:
            logger.warning("Failed to get age breakdown", error=str(e))
            return None

    async def _get_education_data(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get education attainment data."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Education variables (B15003 - Educational Attainment for 25+)
            variables = [
                "B15003_001E",  # Total 25+
                "B15003_017E",  # High school diploma
                "B15003_018E",  # GED
                "B15003_021E",  # Associate's
                "B15003_022E",  # Bachelor's
                "B15003_023E",  # Master's
                "B15003_024E",  # Professional
                "B15003_025E",  # Doctorate
            ]

            if tract_fips:
                geo_filter = f"for=tract:{tract_fips}&in=state:{state_fips}&in=county:{county_fips}"
            else:
                geo_filter = f"for=county:{county_fips}&in=state:{state_fips}"

            url = f"{CENSUS_API_BASE}/{dataset}?get={','.join(variables)}&{geo_filter}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()

            if len(data) >= 2:
                headers = data[0]
                values = data[1]
                value_map = dict(zip(headers, values))

                total = self._safe_int(value_map.get("B15003_001E")) or 1
                hs = self._safe_int(value_map.get("B15003_017E")) + self._safe_int(value_map.get("B15003_018E"))
                associates = self._safe_int(value_map.get("B15003_021E"))
                bachelors = self._safe_int(value_map.get("B15003_022E"))
                graduate = (
                    self._safe_int(value_map.get("B15003_023E")) +
                    self._safe_int(value_map.get("B15003_024E")) +
                    self._safe_int(value_map.get("B15003_025E"))
                )

                college_plus = associates + bachelors + graduate

                return {
                    "high_school_percent": round((hs / total) * 100, 1),
                    "college_plus_percent": round((college_plus / total) * 100, 1),
                    "bachelors_plus_percent": round(((bachelors + graduate) / total) * 100, 1),
                }

            return None
        except Exception as e:
            logger.warning("Failed to get education data", error=str(e))
            return None

    def _safe_int(self, value: Any) -> int:
        """Safely convert value to int."""
        try:
            if value is None:
                return 0
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float."""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# Singleton instance
_census_client: CensusClient | None = None


def get_census_client() -> CensusClient:
    """Get or create the Census client."""
    global _census_client
    if _census_client is None:
        _census_client = CensusClient()
    return _census_client
