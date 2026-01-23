"""Crime data client using city open data portals (Socrata API)."""

import httpx
from typing import Any
from datetime import datetime, timedelta
from ..core.cache import cached
from ..core.logging import get_logger

logger = get_logger("crime")

# City open data portals (Socrata-based)
CITY_CRIME_ENDPOINTS = {
    "new york": {
        "domain": "data.cityofnewyork.us",
        "dataset": "5uac-w243",  # NYPD Complaint Data Current
        "date_field": "cmplnt_fr_dt",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "type_field": "ofns_desc",
    },
    "chicago": {
        "domain": "data.cityofchicago.org",
        "dataset": "ijzp-q8t2",  # Crimes - 2001 to Present
        "date_field": "date",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "type_field": "primary_type",
    },
    "los angeles": {
        "domain": "data.lacity.org",
        "dataset": "2nrs-mtv8",  # Crime Data from 2020 to Present
        "date_field": "date_occ",
        "lat_field": "lat",
        "lng_field": "lon",
        "type_field": "crm_cd_desc",
    },
    "san francisco": {
        "domain": "data.sfgov.org",
        "dataset": "wg3w-h783",  # Police Department Incident Reports
        "date_field": "incident_date",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "type_field": "incident_category",
    },
    "seattle": {
        "domain": "data.seattle.gov",
        "dataset": "tazs-3rd5",  # SPD Crime Data: 2008-Present
        "date_field": "offense_start_datetime",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "type_field": "offense",
    },
    "austin": {
        "domain": "data.austintexas.gov",
        "dataset": "fdj4-gpfu",  # Crime Reports
        "date_field": "occurred_date",
        "lat_field": "latitude",
        "lng_field": "longitude",
        "type_field": "crime_type",
    },
    "denver": {
        "domain": "data.denvergov.org",
        "dataset": "crime",  # Crime data
        "date_field": "reported_date",
        "lat_field": "geo_lat",
        "lng_field": "geo_lon",
        "type_field": "offense_type_id",
    },
    "philadelphia": {
        "domain": "phl.carto.com",  # Different API
        "dataset": "incidents_part1_part2",
        "date_field": "dispatch_date",
        "lat_field": "lat",
        "lng_field": "lng",
        "type_field": "text_general_code",
    },
}

# Crime severity mapping
CRIME_SEVERITY = {
    "violent": ["murder", "homicide", "assault", "robbery", "rape", "kidnapping", "shooting"],
    "property": ["burglary", "theft", "larceny", "vehicle theft", "vandalism", "arson"],
    "other": ["drug", "fraud", "trespass", "disorderly", "prostitution"],
}


class CrimeClient:
    """Client for crime data from city open data portals."""

    _client: httpx.AsyncClient | None = None

    def __init__(self):
        pass

    def _get_client(self) -> httpx.AsyncClient:
        if CrimeClient._client is None:
            CrimeClient._client = httpx.AsyncClient(timeout=30.0)
        return CrimeClient._client

    def _get_city_config(self, city: str) -> dict | None:
        """Get API configuration for a city."""
        city_lower = city.lower().strip()
        for city_name, config in CITY_CRIME_ENDPOINTS.items():
            if city_name in city_lower or city_lower in city_name:
                return config
        return None

    @cached(ttl=43200, key_prefix="crime_nearby")  # Cache for 12 hours
    async def get_crimes_nearby(
        self,
        lat: float,
        lng: float,
        city: str,
        radius_meters: int = 1000,
        days_back: int = 90,
        limit: int = 500,
    ) -> dict[str, Any]:
        """
        Get crimes within a radius of a location.

        Args:
            lat: Latitude
            lng: Longitude
            city: City name
            radius_meters: Search radius in meters
            days_back: How many days back to search
            limit: Maximum results

        Returns:
            Dict with crime counts, types, and safety metrics
        """
        logger.info("Fetching crime data", lat=lat, lng=lng, city=city)

        config = self._get_city_config(city)
        if not config:
            logger.warning("City not supported for crime data", city=city)
            return self._empty_result(city)

        try:
            crimes = await self._fetch_socrata_crimes(lat, lng, config, radius_meters, days_back, limit)
            return self._analyze_crimes(crimes, city, radius_meters)
        except Exception as e:
            logger.error("Crime data fetch failed", error=str(e), city=city)
            return self._empty_result(city)

    async def _fetch_socrata_crimes(
        self,
        lat: float,
        lng: float,
        config: dict,
        radius_meters: int,
        days_back: int,
        limit: int,
    ) -> list[dict]:
        """Fetch crimes from Socrata API."""
        domain = config["domain"]
        dataset = config["dataset"]
        date_field = config["date_field"]
        lat_field = config["lat_field"]
        lng_field = config["lng_field"]

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Socrata query with within_circle function
        radius_km = radius_meters / 1000
        query = f"""
            SELECT *
            WHERE {date_field} >= '{start_date.strftime('%Y-%m-%d')}'
            AND within_circle({lat_field}, {lng_field}, {lat}, {lng}, {radius_km * 1000})
            LIMIT {limit}
        """

        url = f"https://{domain}/resource/{dataset}.json"
        params = {"$query": query}

        response = await self._get_client().get(url, params=params)
        if response.status_code == 200:
            return response.json()

        # Fallback: simple bounding box query if circle query fails
        lat_delta = radius_km / 111  # Approx km per degree
        lng_delta = radius_km / (111 * abs(lat) / 90 if lat != 0 else 111)

        params = {
            "$where": f"{date_field} >= '{start_date.strftime('%Y-%m-%d')}' AND "
            f"{lat_field} BETWEEN {lat - lat_delta} AND {lat + lat_delta} AND "
            f"{lng_field} BETWEEN {lng - lng_delta} AND {lng + lng_delta}",
            "$limit": limit,
        }

        response = await self._get_client().get(url, params=params)
        return response.json() if response.status_code == 200 else []

    def _analyze_crimes(
        self, crimes: list[dict], city: str, radius_meters: int
    ) -> dict[str, Any]:
        """Analyze crime data and compute safety metrics."""
        if not crimes:
            return {
                "city": city,
                "radius_meters": radius_meters,
                "total_crimes": 0,
                "crime_rate": "unknown",
                "safety_score": None,
                "by_type": {},
                "by_severity": {"violent": 0, "property": 0, "other": 0},
                "recommendation": "Insufficient data for analysis",
            }

        config = self._get_city_config(city)
        type_field = config.get("type_field", "type") if config else "type"

        # Count by type
        by_type: dict[str, int] = {}
        by_severity = {"violent": 0, "property": 0, "other": 0}

        for crime in crimes:
            crime_type = str(crime.get(type_field, "unknown")).lower()
            by_type[crime_type] = by_type.get(crime_type, 0) + 1

            # Classify severity
            classified = False
            for severity, keywords in CRIME_SEVERITY.items():
                if any(kw in crime_type for kw in keywords):
                    by_severity[severity] += 1
                    classified = True
                    break
            if not classified:
                by_severity["other"] += 1

        total = len(crimes)
        violent_pct = (by_severity["violent"] / total * 100) if total else 0

        # Compute safety score (0-100, higher is safer)
        # Based on violent crime percentage and total density
        area_sq_km = 3.14159 * (radius_meters / 1000) ** 2
        crimes_per_sq_km = total / area_sq_km if area_sq_km > 0 else 0

        safety_score = max(0, min(100, 100 - (violent_pct * 2) - (crimes_per_sq_km * 0.5)))

        # Determine rating
        if safety_score >= 80:
            crime_rate = "low"
            recommendation = "This area has low crime rates - good for businesses"
        elif safety_score >= 60:
            crime_rate = "moderate"
            recommendation = "Moderate crime levels - standard security measures recommended"
        elif safety_score >= 40:
            crime_rate = "elevated"
            recommendation = "Elevated crime - consider enhanced security measures"
        else:
            crime_rate = "high"
            recommendation = "High crime area - may affect customer foot traffic and require significant security investment"

        return {
            "city": city,
            "radius_meters": radius_meters,
            "total_crimes": total,
            "crime_rate": crime_rate,
            "safety_score": round(safety_score, 1),
            "by_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_severity": by_severity,
            "violent_crime_pct": round(violent_pct, 1),
            "crimes_per_sq_km": round(crimes_per_sq_km, 1),
            "recommendation": recommendation,
        }

    def _empty_result(self, city: str) -> dict[str, Any]:
        """Return empty result structure."""
        return {
            "city": city,
            "total_crimes": 0,
            "crime_rate": "unknown",
            "safety_score": None,
            "by_type": {},
            "by_severity": {"violent": 0, "property": 0, "other": 0},
            "recommendation": f"Crime data not available for {city}. Consider checking local police department records.",
        }

    def get_supported_cities(self) -> list[str]:
        """Return list of cities with crime data support."""
        return list(CITY_CRIME_ENDPOINTS.keys())


_crime_client: CrimeClient | None = None


def get_crime_client() -> CrimeClient:
    global _crime_client
    if _crime_client is None:
        _crime_client = CrimeClient()
    return _crime_client
