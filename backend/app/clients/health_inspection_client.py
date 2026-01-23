"""Health inspection data client using city open data portals."""

import httpx
from typing import Any
from datetime import datetime
from ..core.cache import cached
from ..core.logging import get_logger

logger = get_logger("health_inspection")

# City health inspection data endpoints
CITY_HEALTH_ENDPOINTS = {
    "new york": {
        "domain": "data.cityofnewyork.us",
        "dataset": "43nn-pn8j",  # DOHMH Restaurant Inspection Results
        "name_field": "dba",
        "address_field": "building",
        "street_field": "street",
        "score_field": "score",
        "grade_field": "grade",
        "date_field": "inspection_date",
        "violation_field": "violation_description",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "cuisine_field": "cuisine_description",
    },
    "chicago": {
        "domain": "data.cityofchicago.org",
        "dataset": "4ijn-s7e5",  # Food Inspections
        "name_field": "dba_name",
        "address_field": "address",
        "score_field": None,  # Chicago uses pass/fail
        "grade_field": "results",
        "date_field": "inspection_date",
        "violation_field": "violations",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "cuisine_field": "facility_type",
    },
    "san francisco": {
        "domain": "data.sfgov.org",
        "dataset": "pyih-qa8i",  # Restaurant Scores LIVES Standard
        "name_field": "business_name",
        "address_field": "business_address",
        "score_field": "inspection_score",
        "grade_field": None,
        "date_field": "inspection_date",
        "violation_field": "violation_description",
        "lat_field": "business_latitude",
        "lng_field": "business_longitude",
        "cuisine_field": None,
    },
    "los angeles": {
        "domain": "data.lacounty.gov",
        "dataset": "rikz-3aea",  # Restaurant and Market Inspections
        "name_field": "facility_name",
        "address_field": "facility_address",
        "score_field": "score",
        "grade_field": "grade",
        "date_field": "activity_date",
        "violation_field": "violation_description",
        "lat_field": "facility_latitude",
        "lng_field": "facility_longitude",
        "cuisine_field": None,
    },
    "seattle": {
        "domain": "data.kingcounty.gov",
        "dataset": "f29f-zza5",  # Food Establishment Inspection Data
        "name_field": "name",
        "address_field": "address",
        "score_field": "inspection_score",
        "grade_field": "grade",
        "date_field": "inspection_date",
        "violation_field": "violation_description",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "cuisine_field": "description",
    },
    "austin": {
        "domain": "data.austintexas.gov",
        "dataset": "ecmv-9xxi",  # Food Establishment Inspection Scores
        "name_field": "restaurant_name",
        "address_field": "address",
        "score_field": "score",
        "grade_field": None,
        "date_field": "inspection_date",
        "violation_field": None,
        "lat_field": "latitude",
        "lng_field": "longitude",
        "cuisine_field": None,
    },
}


class HealthInspectionClient:
    """Client for health inspection data from city open data portals."""

    _client: httpx.AsyncClient | None = None

    def __init__(self):
        pass

    def _get_client(self) -> httpx.AsyncClient:
        if HealthInspectionClient._client is None:
            HealthInspectionClient._client = httpx.AsyncClient(timeout=30.0)
        return HealthInspectionClient._client

    def _get_city_config(self, city: str) -> dict | None:
        """Get API configuration for a city."""
        city_lower = city.lower().strip()
        for city_name, config in CITY_HEALTH_ENDPOINTS.items():
            if city_name in city_lower or city_lower in city_name:
                return {**config, "city_name": city_name}
        return None

    @cached(ttl=86400, key_prefix="health_nearby")  # Cache for 24 hours
    async def get_inspections_nearby(
        self,
        lat: float,
        lng: float,
        city: str,
        radius_meters: int = 1000,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get health inspection data for restaurants near a location.

        Args:
            lat: Latitude
            lng: Longitude
            city: City name
            radius_meters: Search radius in meters
            limit: Maximum results

        Returns:
            Dict with inspection data and area statistics
        """
        logger.info("Fetching health inspections", lat=lat, lng=lng, city=city)

        config = self._get_city_config(city)
        if not config:
            logger.warning("City not supported for health data", city=city)
            return self._empty_result(city)

        try:
            inspections = await self._fetch_inspections(lat, lng, config, radius_meters, limit)
            return self._analyze_inspections(inspections, config, city, radius_meters)
        except Exception as e:
            logger.error("Health inspection fetch failed", error=str(e), city=city)
            return self._empty_result(city)

    async def _fetch_inspections(
        self, lat: float, lng: float, config: dict, radius_meters: int, limit: int
    ) -> list[dict]:
        """Fetch inspections from Socrata API."""
        domain = config["domain"]
        dataset = config["dataset"]
        lat_field = config["lat_field"]
        lng_field = config["lng_field"]

        radius_km = radius_meters / 1000
        url = f"https://{domain}/resource/{dataset}.json"

        # Try within_circle query first
        query = f"""
            SELECT *
            WHERE within_circle({lat_field}, {lng_field}, {lat}, {lng}, {radius_km * 1000})
            ORDER BY {config['date_field']} DESC
            LIMIT {limit}
        """
        params = {"$query": query}

        response = await self._get_client().get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data

        # Fallback: bounding box query
        lat_delta = radius_km / 111
        lng_delta = radius_km / 85  # Approximate at mid-latitudes

        params = {
            "$where": f"{lat_field} BETWEEN {lat - lat_delta} AND {lat + lat_delta} AND "
            f"{lng_field} BETWEEN {lng - lng_delta} AND {lng + lng_delta}",
            "$order": f"{config['date_field']} DESC",
            "$limit": limit,
        }

        response = await self._get_client().get(url, params=params)
        return response.json() if response.status_code == 200 else []

    def _analyze_inspections(
        self, inspections: list[dict], config: dict, city: str, radius_meters: int
    ) -> dict[str, Any]:
        """Analyze inspection data and compute statistics."""
        if not inspections:
            return self._empty_result(city)

        score_field = config.get("score_field")
        grade_field = config.get("grade_field")
        name_field = config.get("name_field", "name")
        address_field = config.get("address_field", "address")
        date_field = config.get("date_field", "inspection_date")

        scores = []
        grades: dict[str, int] = {}
        restaurants: list[dict] = []
        seen_names: set[str] = set()

        for insp in inspections:
            name = insp.get(name_field, "Unknown")

            # Skip duplicates (keep most recent)
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            score = None
            if score_field and insp.get(score_field):
                try:
                    score = float(insp[score_field])
                    scores.append(score)
                except (ValueError, TypeError):
                    pass

            grade = None
            if grade_field:
                grade = insp.get(grade_field)
                if grade:
                    grades[grade] = grades.get(grade, 0) + 1

            restaurants.append({
                "name": name,
                "address": insp.get(address_field, ""),
                "score": score,
                "grade": grade,
                "inspection_date": insp.get(date_field),
                "lat": insp.get(config["lat_field"]),
                "lng": insp.get(config["lng_field"]),
            })

        avg_score = sum(scores) / len(scores) if scores else None
        total_restaurants = len(restaurants)

        # Determine area health rating
        if avg_score is not None:
            if avg_score >= 90:
                health_rating = "excellent"
                insight = "Restaurants in this area maintain high hygiene standards"
            elif avg_score >= 80:
                health_rating = "good"
                insight = "Good overall hygiene - most restaurants pass inspections"
            elif avg_score >= 70:
                health_rating = "fair"
                insight = "Mixed results - some restaurants have violations"
            else:
                health_rating = "poor"
                insight = "Below average - consider this when selecting a location"
        else:
            health_rating = "unknown"
            insight = "Inspection scores not available for this area"

        return {
            "city": city,
            "radius_meters": radius_meters,
            "total_restaurants": total_restaurants,
            "avg_score": round(avg_score, 1) if avg_score else None,
            "health_rating": health_rating,
            "grade_distribution": grades,
            "insight": insight,
            "restaurants": restaurants[:20],  # Top 20 only
            "score_field_used": score_field is not None,
        }

    def _empty_result(self, city: str) -> dict[str, Any]:
        """Return empty result structure."""
        return {
            "city": city,
            "total_restaurants": 0,
            "avg_score": None,
            "health_rating": "unknown",
            "grade_distribution": {},
            "insight": f"Health inspection data not available for {city}",
            "restaurants": [],
        }

    @cached(ttl=86400, key_prefix="health_business")
    async def get_business_inspections(
        self, business_name: str, city: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get inspection history for a specific business.

        Args:
            business_name: Name of the business
            city: City name
            limit: Maximum results

        Returns:
            List of inspection records
        """
        config = self._get_city_config(city)
        if not config:
            return []

        domain = config["domain"]
        dataset = config["dataset"]
        name_field = config["name_field"]
        url = f"https://{domain}/resource/{dataset}.json"

        params = {
            "$where": f"upper({name_field}) LIKE '%{business_name.upper()}%'",
            "$order": f"{config['date_field']} DESC",
            "$limit": limit,
        }

        try:
            response = await self._get_client().get(url, params=params)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error("Business inspection fetch failed", error=str(e))

        return []

    def get_supported_cities(self) -> list[str]:
        """Return list of cities with health inspection data support."""
        return list(CITY_HEALTH_ENDPOINTS.keys())


_health_inspection_client: HealthInspectionClient | None = None


def get_health_inspection_client() -> HealthInspectionClient:
    global _health_inspection_client
    if _health_inspection_client is None:
        _health_inspection_client = HealthInspectionClient()
    return _health_inspection_client
