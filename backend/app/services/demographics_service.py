"""Service for fetching and managing demographic data."""

from typing import Any
from ..tools.market_validator.census_client import get_census_client
from ..tools.location_scout.google_maps import GoogleMapsClient
from ..core.logging import get_logger
from ..core.cache import cached

logger = get_logger("demographics_service")


class DemographicsService:
    """Service for fetching comprehensive demographic data for locations."""

    def __init__(self):
        self.census = get_census_client()
        self.maps = GoogleMapsClient()

    @cached(ttl=86400, key_prefix="demographics_full")  # Cache for 24 hours
    async def get_demographics_for_address(self, address: str) -> dict[str, Any]:
        """
        Get comprehensive demographic data for an address.

        Returns demographics including:
        - Population & density
        - Income distribution
        - Age breakdown
        - Education levels
        - Race/ethnicity
        - Household composition
        - Employment & industry
        - Commute patterns
        """
        try:
            # Geocode the address
            geocode_result = await self.maps.geocode(address)
            if not geocode_result:
                return {"error": "Could not geocode address", "demographics": None}

            lat = geocode_result["lat"]
            lng = geocode_result["lng"]

            # Get Census geography for coordinates
            geography = await self.census.get_geography_for_coordinates(lat, lng)
            if not geography:
                return {"error": "Could not determine Census geography", "demographics": None}

            # Get full demographics from Census
            demographics = await self.census.get_demographics(
                state_fips=geography["state_fips"],
                county_fips=geography["county_fips"],
                tract_fips=geography.get("tract_fips"),
            )

            # Add location context
            demographics["location"] = {
                "address": geocode_result.get("formatted_address", address),
                "county": geography.get("county_name", ""),
                "state": geography.get("state_name", ""),
                "coordinates": {"lat": lat, "lng": lng},
            }

            return {
                "success": True,
                "demographics": demographics,
            }

        except Exception as e:
            logger.error("Failed to get demographics for address", address=address, error=str(e))
            return {"error": str(e), "demographics": None}

    async def get_demographics_summary(self, demographics: dict[str, Any]) -> dict[str, Any]:
        """
        Create a summary of key demographic indicators for display.

        Takes full demographics and returns a simplified summary with categorical labels.
        """
        if not demographics:
            return {}

        summary = {}

        # Income level
        if demographics.get("income"):
            median_income = demographics["income"].get("median_household", 0)
            if median_income >= 100000:
                summary["income_level"] = "high"
            elif median_income >= 75000:
                summary["income_level"] = "above average"
            elif median_income >= 50000:
                summary["income_level"] = "moderate"
            else:
                summary["income_level"] = "below average"

        # Age profile
        if demographics.get("age_distribution"):
            age = demographics["age_distribution"]
            median_age = age.get("median_age", 0)
            young_adults = age.get("age_18_34_percent", 0)
            if median_age < 30 or young_adults > 30:
                summary["age_profile"] = "young_professional"
            elif median_age < 40:
                summary["age_profile"] = "working_age"
            elif median_age < 55:
                summary["age_profile"] = "established"
            else:
                summary["age_profile"] = "mature"

        # Education level
        if demographics.get("education"):
            bachelors = demographics["education"].get("bachelors_plus_percent", 0)
            if bachelors >= 50:
                summary["education_level"] = "highly educated"
            elif bachelors >= 30:
                summary["education_level"] = "well educated"
            else:
                summary["education_level"] = "diverse"

        # Density type
        if demographics.get("population"):
            density = demographics["population"].get("density", 0)
            if density >= 10000:
                summary["density_type"] = "urban core"
            elif density >= 5000:
                summary["density_type"] = "urban"
            elif density >= 1000:
                summary["density_type"] = "suburban"
            else:
                summary["density_type"] = "rural"

        return summary

    def calculate_demographic_fit_score(
        self, demographics: dict[str, Any], business_type: str
    ) -> dict[str, Any]:
        """
        Calculate how well the demographics fit a business type.

        Returns a score and explanation.
        """
        if not demographics:
            return {"score": 0, "factors": [], "fit_level": "Unknown"}

        score = 50  # Base score
        factors = []

        income = demographics.get("income", {})
        education = demographics.get("education", {})
        age = demographics.get("age_distribution", {})
        employment = demographics.get("employment", {})
        households = demographics.get("households", {})

        median_income = income.get("median_household", 0)
        college_percent = education.get("college_plus_percent", 0)
        young_adults = age.get("age_18_34_percent", 0)
        employment_rate = employment.get("employment_rate", 0)

        # Business-type specific scoring
        business_lower = business_type.lower()

        # High-income businesses
        if any(word in business_lower for word in ["luxury", "premium", "boutique", "spa", "fine dining"]):
            if median_income > 100000:
                score += 20
                factors.append("High median income supports premium pricing")
            elif median_income > 75000:
                score += 10
                factors.append("Above-average income level")
            else:
                score -= 10
                factors.append("Income may limit premium market potential")

        # Youth-oriented businesses
        if any(word in business_lower for word in ["nightclub", "bar", "gaming", "fitness", "gym"]):
            if young_adults > 30:
                score += 15
                factors.append("Strong young adult population")
            elif young_adults > 20:
                score += 5
                factors.append("Moderate young adult presence")
            else:
                score -= 10
                factors.append("Limited young adult demographic")

        # Family-oriented businesses
        if any(word in business_lower for word in ["daycare", "pediatric", "family", "kids", "toy"]):
            family_percent = households.get("family_households_percent", 0)
            if family_percent > 60:
                score += 20
                factors.append("High concentration of family households")
            elif family_percent > 45:
                score += 10
                factors.append("Good family household presence")
            else:
                factors.append("Consider targeting non-family demographics too")

        # Professional services
        if any(word in business_lower for word in ["consulting", "law", "accounting", "tech", "coworking"]):
            if college_percent > 40:
                score += 15
                factors.append("Highly educated population")
            if employment_rate > 95:
                score += 10
                factors.append("Low unemployment indicates healthy economy")

        # General factors
        if employment_rate > 95:
            score += 5
            factors.append("Strong local employment")
        elif employment_rate < 90:
            score -= 5
            factors.append("Higher unemployment may affect spending")

        # Determine fit level
        if score >= 80:
            fit_level = "Excellent"
        elif score >= 65:
            fit_level = "Good"
        elif score >= 50:
            fit_level = "Moderate"
        else:
            fit_level = "Challenging"

        return {
            "score": min(100, max(0, score)),
            "fit_level": fit_level,
            "factors": factors,
        }


# Singleton instance
_demographics_service: DemographicsService | None = None


def get_demographics_service() -> DemographicsService:
    """Get or create the demographics service."""
    global _demographics_service
    if _demographics_service is None:
        _demographics_service = DemographicsService()
    return _demographics_service
