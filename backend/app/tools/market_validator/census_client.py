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
    async def get_geography_for_coordinates(self, lat: float, lng: float) -> dict[str, Any] | None:
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
            "race_ethnicity": {},
            "households": {},
            "employment": {},
            "commute": {},
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

            # Get race/ethnicity data
            race_data = await self._get_race_ethnicity(state_fips, county_fips, tract_fips)
            if race_data:
                demographics["race_ethnicity"] = race_data

            # Get household composition data
            household_data = await self._get_household_data(state_fips, county_fips, tract_fips)
            if household_data:
                demographics["households"] = household_data

            # Get employment data
            employment_data = await self._get_employment_data(state_fips, county_fips, tract_fips)
            if employment_data:
                demographics["employment"] = employment_data

            # Get commute/transportation data
            commute_data = await self._get_commute_data(state_fips, county_fips, tract_fips)
            if commute_data:
                demographics["commute"] = commute_data

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
                "B01001_003E",
                "B01001_004E",
                "B01001_005E",
                "B01001_006E",  # Male under 18
                "B01001_027E",
                "B01001_028E",
                "B01001_029E",
                "B01001_030E",  # Female under 18
                "B01001_007E",
                "B01001_008E",
                "B01001_009E",
                "B01001_010E",
                "B01001_011E",
                "B01001_012E",  # Male 18-34
                "B01001_031E",
                "B01001_032E",
                "B01001_033E",
                "B01001_034E",
                "B01001_035E",
                "B01001_036E",  # Female 18-34
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
                under_18_vars = [
                    "B01001_003E",
                    "B01001_004E",
                    "B01001_005E",
                    "B01001_006E",
                    "B01001_027E",
                    "B01001_028E",
                    "B01001_029E",
                    "B01001_030E",
                ]
                under_18 = sum(self._safe_int(value_map.get(v)) for v in under_18_vars)

                # Calculate 18-34
                age_18_34_vars = [
                    "B01001_007E",
                    "B01001_008E",
                    "B01001_009E",
                    "B01001_010E",
                    "B01001_011E",
                    "B01001_012E",
                    "B01001_031E",
                    "B01001_032E",
                    "B01001_033E",
                    "B01001_034E",
                    "B01001_035E",
                    "B01001_036E",
                ]
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
                hs = self._safe_int(value_map.get("B15003_017E")) + self._safe_int(
                    value_map.get("B15003_018E")
                )
                associates = self._safe_int(value_map.get("B15003_021E"))
                bachelors = self._safe_int(value_map.get("B15003_022E"))
                graduate = (
                    self._safe_int(value_map.get("B15003_023E"))
                    + self._safe_int(value_map.get("B15003_024E"))
                    + self._safe_int(value_map.get("B15003_025E"))
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

    async def _get_race_ethnicity(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get race and ethnicity breakdown."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Race variables (B02001)
            variables = [
                "B02001_001E",  # Total
                "B02001_002E",  # White alone
                "B02001_003E",  # Black/African American alone
                "B02001_004E",  # American Indian/Alaska Native alone
                "B02001_005E",  # Asian alone
                "B02001_006E",  # Native Hawaiian/Pacific Islander alone
                "B02001_007E",  # Some other race alone
                "B02001_008E",  # Two or more races
                "B03003_001E",  # Hispanic/Latino total
                "B03003_003E",  # Hispanic/Latino
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

                total = self._safe_int(value_map.get("B02001_001E")) or 1

                return {
                    "white_percent": round((self._safe_int(value_map.get("B02001_002E")) / total) * 100, 1),
                    "black_percent": round((self._safe_int(value_map.get("B02001_003E")) / total) * 100, 1),
                    "asian_percent": round((self._safe_int(value_map.get("B02001_005E")) / total) * 100, 1),
                    "hispanic_percent": round((self._safe_int(value_map.get("B03003_003E")) / total) * 100, 1),
                    "other_percent": round(
                        (
                            self._safe_int(value_map.get("B02001_004E"))
                            + self._safe_int(value_map.get("B02001_006E"))
                            + self._safe_int(value_map.get("B02001_007E"))
                            + self._safe_int(value_map.get("B02001_008E"))
                        )
                        / total
                        * 100,
                        1,
                    ),
                }

            return None
        except Exception as e:
            logger.warning("Failed to get race/ethnicity data", error=str(e))
            return None

    async def _get_household_data(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get household composition data."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Household variables (B11001, B25010)
            variables = [
                "B11001_001E",  # Total households
                "B11001_002E",  # Family households
                "B11001_003E",  # Married-couple family
                "B11001_004E",  # Other family (male householder, no spouse)
                "B11001_005E",  # Other family (female householder, no spouse)
                "B11001_007E",  # Nonfamily households
                "B25010_001E",  # Average household size
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

                total = self._safe_int(value_map.get("B11001_001E")) or 1
                families = self._safe_int(value_map.get("B11001_002E"))
                married = self._safe_int(value_map.get("B11001_003E"))
                nonfamily = self._safe_int(value_map.get("B11001_007E"))

                return {
                    "total_households": total,
                    "family_households_percent": round((families / total) * 100, 1),
                    "married_couples_percent": round((married / total) * 100, 1),
                    "single_person_percent": round((nonfamily / total) * 100, 1),
                    "average_household_size": self._safe_float(value_map.get("B25010_001E")),
                }

            return None
        except Exception as e:
            logger.warning("Failed to get household data", error=str(e))
            return None

    async def _get_employment_data(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get employment and industry data."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Employment variables (B23025, C24030)
            variables = [
                "B23025_001E",  # Total population 16+
                "B23025_002E",  # In labor force
                "B23025_003E",  # Civilian labor force
                "B23025_004E",  # Employed
                "B23025_005E",  # Unemployed
                "C24030_001E",  # Total workers
                "C24030_003E",  # Management/business/science/arts
                "C24030_017E",  # Service
                "C24030_031E",  # Sales/office
                "C24030_045E",  # Natural resources/construction/maintenance
                "C24030_059E",  # Production/transportation
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

                pop_16plus = self._safe_int(value_map.get("B23025_001E")) or 1
                labor_force = self._safe_int(value_map.get("B23025_002E"))
                employed = self._safe_int(value_map.get("B23025_004E"))
                unemployed = self._safe_int(value_map.get("B23025_005E"))
                total_workers = self._safe_int(value_map.get("C24030_001E")) or 1

                return {
                    "labor_force_participation": round((labor_force / pop_16plus) * 100, 1),
                    "employment_rate": round((employed / labor_force) * 100, 1) if labor_force else 0,
                    "unemployment_rate": round((unemployed / labor_force) * 100, 1) if labor_force else 0,
                    "industry_breakdown": {
                        "management_business_percent": round(
                            (self._safe_int(value_map.get("C24030_003E")) / total_workers) * 100, 1
                        ),
                        "service_percent": round(
                            (self._safe_int(value_map.get("C24030_017E")) / total_workers) * 100, 1
                        ),
                        "sales_office_percent": round(
                            (self._safe_int(value_map.get("C24030_031E")) / total_workers) * 100, 1
                        ),
                        "construction_percent": round(
                            (self._safe_int(value_map.get("C24030_045E")) / total_workers) * 100, 1
                        ),
                        "production_transport_percent": round(
                            (self._safe_int(value_map.get("C24030_059E")) / total_workers) * 100, 1
                        ),
                    },
                }

            return None
        except Exception as e:
            logger.warning("Failed to get employment data", error=str(e))
            return None

    async def _get_commute_data(
        self, state_fips: str, county_fips: str, tract_fips: str | None = None
    ) -> dict[str, Any] | None:
        """Get commute and transportation data."""
        try:
            year = "2022"
            dataset = f"{year}/acs/acs5"

            # Commute variables (B08301, B08303)
            variables = [
                "B08301_001E",  # Total workers 16+
                "B08301_002E",  # Car, truck, or van (drove alone)
                "B08301_003E",  # Car, truck, or van (carpooled)
                "B08301_010E",  # Public transportation
                "B08301_018E",  # Bicycle
                "B08301_019E",  # Walked
                "B08301_021E",  # Worked from home
                "B08303_001E",  # Total for travel time
                "B08303_008E",  # 15-19 minutes
                "B08303_009E",  # 20-24 minutes
                "B08303_010E",  # 25-29 minutes
                "B08303_011E",  # 30-34 minutes
                "B08303_012E",  # 35-44 minutes
                "B08303_013E",  # 45+ minutes
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

                total = self._safe_int(value_map.get("B08301_001E")) or 1
                total_time = self._safe_int(value_map.get("B08303_001E")) or 1

                # Calculate long commuters (30+ minutes)
                long_commute = (
                    self._safe_int(value_map.get("B08303_011E"))
                    + self._safe_int(value_map.get("B08303_012E"))
                    + self._safe_int(value_map.get("B08303_013E"))
                )

                return {
                    "drive_alone_percent": round(
                        (self._safe_int(value_map.get("B08301_002E")) / total) * 100, 1
                    ),
                    "carpool_percent": round(
                        (self._safe_int(value_map.get("B08301_003E")) / total) * 100, 1
                    ),
                    "public_transit_percent": round(
                        (self._safe_int(value_map.get("B08301_010E")) / total) * 100, 1
                    ),
                    "walk_bike_percent": round(
                        (
                            self._safe_int(value_map.get("B08301_018E"))
                            + self._safe_int(value_map.get("B08301_019E"))
                        )
                        / total
                        * 100,
                        1,
                    ),
                    "work_from_home_percent": round(
                        (self._safe_int(value_map.get("B08301_021E")) / total) * 100, 1
                    ),
                    "long_commute_percent": round((long_commute / total_time) * 100, 1),
                }

            return None
        except Exception as e:
            logger.warning("Failed to get commute data", error=str(e))
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
