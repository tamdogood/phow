"""Celery tasks for background data collection and processing."""

import asyncio
from typing import Any
import geohash as gh
from .celery_app import celery_app
from ..core.logging import get_logger
from ..core.config import get_settings
from ..api.deps import get_supabase
from ..clients import (
    get_walkscore_client,
    get_crime_client,
    get_health_inspection_client,
    get_trends_client,
)
from ..services.embedding_service import get_embedding_service
from ..repositories.location_intelligence_repository import LocationIntelligenceRepository

logger = get_logger("celery_tasks")

# Target cities for data collection (Phase 1)
TARGET_CITIES = [
    ("New York", "NY", 40.7128, -74.0060),
    ("Los Angeles", "CA", 34.0522, -118.2437),
    ("Chicago", "IL", 41.8781, -87.6298),
    ("Houston", "TX", 29.7604, -95.3698),
    ("Phoenix", "AZ", 33.4484, -112.0740),
    ("Philadelphia", "PA", 39.9526, -75.1652),
    ("San Antonio", "TX", 29.4241, -98.4936),
    ("San Diego", "CA", 32.7157, -117.1611),
    ("Dallas", "TX", 32.7767, -96.7970),
    ("San Jose", "CA", 37.3382, -121.8863),
    ("Austin", "TX", 30.2672, -97.7431),
    ("Jacksonville", "FL", 30.3322, -81.6557),
    ("Fort Worth", "TX", 32.7555, -97.3308),
    ("Columbus", "OH", 39.9612, -82.9988),
    ("Charlotte", "NC", 35.2271, -80.8431),
    ("San Francisco", "CA", 37.7749, -122.4194),
    ("Indianapolis", "IN", 39.7684, -86.1581),
    ("Seattle", "WA", 47.6062, -122.3321),
    ("Denver", "CO", 39.7392, -104.9903),
    ("Washington", "DC", 38.9072, -77.0369),
]


def run_async(coro):
    """Helper to run async functions in Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def collect_crime_data(self, city: str, state: str, lat: float, lng: float) -> dict[str, Any]:
    """
    Collect crime data for a city and store with embeddings.

    Args:
        city: City name
        state: State abbreviation
        lat: City center latitude
        lng: City center longitude

    Returns:
        Collection result summary
    """
    logger.info("Collecting crime data", city=city, state=state)

    try:
        async def _collect():
            client = get_crime_client()
            db = get_supabase()
            embedding_service = get_embedding_service(db)
            intel_repo = LocationIntelligenceRepository(db)

            # Collect crime data
            crime_data = await client.get_crimes_nearby(lat, lng, city)

            if crime_data.get("total_crimes", 0) > 0 or crime_data.get("safety_score"):
                geohash = gh.encode(lat, lng, precision=6)

                # Store structured data
                await intel_repo.upsert(
                    geohash=geohash,
                    data_type="crime",
                    data=crime_data,
                    source="city_open_data",
                    lat=lat,
                    lng=lng,
                    city=city,
                    state=state,
                    valid_days=1,  # Crime data refreshed daily
                )

                # Generate and store embedding
                await embedding_service.embed_crime_data(crime_data, lat, lng, city)

                return {
                    "status": "success",
                    "city": city,
                    "total_crimes": crime_data.get("total_crimes"),
                    "safety_score": crime_data.get("safety_score"),
                }

            return {"status": "no_data", "city": city}

        return run_async(_collect())

    except Exception as e:
        logger.error("Crime data collection failed", city=city, error=str(e))
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def collect_health_inspections(self, city: str, state: str, lat: float, lng: float) -> dict[str, Any]:
    """
    Collect health inspection data for a city.

    Args:
        city: City name
        state: State abbreviation
        lat: City center latitude
        lng: City center longitude

    Returns:
        Collection result summary
    """
    logger.info("Collecting health inspections", city=city, state=state)

    try:
        async def _collect():
            client = get_health_inspection_client()
            db = get_supabase()
            embedding_service = get_embedding_service(db)
            intel_repo = LocationIntelligenceRepository(db)

            # Collect health data with larger radius for city-wide stats
            health_data = await client.get_inspections_nearby(lat, lng, city, radius_meters=5000)

            if health_data.get("total_restaurants", 0) > 0:
                geohash = gh.encode(lat, lng, precision=6)

                # Store structured data
                await intel_repo.upsert(
                    geohash=geohash,
                    data_type="health",
                    data=health_data,
                    source="city_open_data",
                    lat=lat,
                    lng=lng,
                    city=city,
                    state=state,
                    valid_days=7,  # Health data refreshed weekly
                )

                # Generate and store embedding
                await embedding_service.embed_health_inspection(health_data, lat, lng, city)

                return {
                    "status": "success",
                    "city": city,
                    "total_restaurants": health_data.get("total_restaurants"),
                    "avg_score": health_data.get("avg_score"),
                }

            return {"status": "no_data", "city": city}

        return run_async(_collect())

    except Exception as e:
        logger.error("Health inspection collection failed", city=city, error=str(e))
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def collect_walkscore(self, lat: float, lng: float, city: str, address: str | None = None) -> dict[str, Any]:
    """
    Collect Walk Score data for a location.

    Args:
        lat: Latitude
        lng: Longitude
        city: City name
        address: Optional address

    Returns:
        Collection result summary
    """
    logger.info("Collecting Walk Score", lat=lat, lng=lng, city=city)

    try:
        async def _collect():
            client = get_walkscore_client()
            db = get_supabase()
            embedding_service = get_embedding_service(db)
            intel_repo = LocationIntelligenceRepository(db)

            score_data = await client.get_score(lat, lng, address)

            if score_data and score_data.get("walkscore"):
                geohash = gh.encode(lat, lng, precision=7)

                # Store structured data
                await intel_repo.upsert(
                    geohash=geohash,
                    data_type="walkscore",
                    data=score_data,
                    source="walkscore_api",
                    lat=lat,
                    lng=lng,
                    city=city,
                    valid_days=30,  # Walk scores rarely change
                )

                # Generate and store embedding
                await embedding_service.embed_walkscore(score_data, lat, lng, city)

                return {
                    "status": "success",
                    "walkscore": score_data.get("walkscore"),
                    "transit_score": score_data.get("transit_score"),
                }

            return {"status": "no_data"}

        return run_async(_collect())

    except Exception as e:
        logger.error("Walk Score collection failed", lat=lat, lng=lng, error=str(e))
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def collect_search_trends(self, keywords: list[str], city: str | None = None) -> dict[str, Any]:
    """
    Collect Google Trends data for keywords.

    Args:
        keywords: Search terms to analyze
        city: Optional city filter

    Returns:
        Collection result summary
    """
    logger.info("Collecting search trends", keywords=keywords, city=city)

    try:
        async def _collect():
            client = get_trends_client()
            db = get_supabase()
            embedding_service = get_embedding_service(db)
            intel_repo = LocationIntelligenceRepository(db)

            # Get interest over time
            trends_data = await client.get_interest_over_time(keywords, city)

            if trends_data.get("data"):
                # Use city center if available, otherwise generic
                lat, lng = None, None
                for c, s, clat, clng in TARGET_CITIES:
                    if city and city.lower() in c.lower():
                        lat, lng = clat, clng
                        break

                geohash = gh.encode(lat, lng, precision=4) if lat and lng else "us"

                # Store structured data
                await intel_repo.upsert(
                    geohash=geohash,
                    data_type="trends",
                    data=trends_data,
                    source="google_trends",
                    lat=lat,
                    lng=lng,
                    city=city or "US",
                    valid_days=7,  # Trends refreshed weekly
                )

                # Generate and store embedding
                await embedding_service.embed_trends(trends_data, lat, lng, city or "US")

                return {
                    "status": "success",
                    "keywords": keywords,
                    "data_points": len(trends_data.get("data", [])),
                }

            return {"status": "no_data", "keywords": keywords}

        return run_async(_collect())

    except Exception as e:
        logger.error("Trends collection failed", keywords=keywords, error=str(e))
        raise self.retry(exc=e, countdown=60)


@celery_app.task
def refresh_all_city_data() -> dict[str, Any]:
    """
    Refresh location intelligence data for all target cities.
    Scheduled task to run daily.

    Returns:
        Summary of refresh results
    """
    logger.info("Starting full city data refresh")

    results = {"cities_processed": 0, "errors": []}

    for city, state, lat, lng in TARGET_CITIES:
        try:
            # Queue crime data collection
            collect_crime_data.delay(city, state, lat, lng)

            # Queue health inspection collection
            collect_health_inspections.delay(city, state, lat, lng)

            # Queue Walk Score for city center
            collect_walkscore.delay(lat, lng, city)

            results["cities_processed"] += 1
        except Exception as e:
            logger.error("Failed to queue tasks for city", city=city, error=str(e))
            results["errors"].append({"city": city, "error": str(e)})

    logger.info("City data refresh queued", results=results)
    return results


@celery_app.task
def refresh_trends_data(keywords: list[str] | None = None) -> dict[str, Any]:
    """
    Refresh Google Trends data for F&B keywords.
    Scheduled task to run weekly.

    Args:
        keywords: Optional custom keywords, uses defaults if not provided

    Returns:
        Summary of refresh results
    """
    # Default F&B trending keywords
    default_keywords = [
        ["coffee shop", "cafe near me"],
        ["pizza delivery", "pizza restaurant"],
        ["boba tea", "bubble tea"],
        ["sushi restaurant", "japanese food"],
        ["mexican restaurant", "tacos near me"],
        ["burger restaurant", "best burgers"],
        ["healthy food", "salad restaurant"],
        ["food delivery", "takeout near me"],
    ]

    keywords_to_process = [keywords] if keywords else default_keywords

    logger.info("Starting trends refresh", keyword_groups=len(keywords_to_process))

    results = {"groups_processed": 0, "errors": []}

    for kw_group in keywords_to_process:
        try:
            # National trends
            collect_search_trends.delay(kw_group, None)

            # City-specific trends for major markets
            for city in ["New York", "Los Angeles", "Chicago", "San Francisco", "Austin"]:
                collect_search_trends.delay(kw_group, city)

            results["groups_processed"] += 1
        except Exception as e:
            logger.error("Failed to queue trends task", keywords=kw_group, error=str(e))
            results["errors"].append({"keywords": kw_group, "error": str(e)})

    return results


@celery_app.task
def cleanup_expired_data() -> dict[str, Any]:
    """
    Clean up expired location intelligence data and embeddings.
    Scheduled task to run daily.

    Returns:
        Cleanup statistics
    """
    logger.info("Starting data cleanup")

    async def _cleanup():
        db = get_supabase()
        intel_repo = LocationIntelligenceRepository(db)
        from ..repositories.location_intelligence_repository import DataEmbeddingRepository

        embedding_repo = DataEmbeddingRepository(db)

        intel_deleted = await intel_repo.delete_expired()
        embeddings_deleted = await embedding_repo.delete_expired()

        return {
            "intelligence_records_deleted": intel_deleted,
            "embeddings_deleted": embeddings_deleted,
        }

    result = run_async(_cleanup())
    logger.info("Data cleanup complete", result=result)
    return result


# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "refresh-city-data-daily": {
        "task": "app.workers.tasks.refresh_all_city_data",
        "schedule": 86400,  # Every 24 hours
        "options": {"queue": "data_collection"},
    },
    "refresh-trends-weekly": {
        "task": "app.workers.tasks.refresh_trends_data",
        "schedule": 604800,  # Every 7 days
        "options": {"queue": "data_collection"},
    },
    "cleanup-expired-daily": {
        "task": "app.workers.tasks.cleanup_expired_data",
        "schedule": 86400,  # Every 24 hours
        "options": {"queue": "maintenance"},
    },
    "sync-reviews-15-min": {
        "task": "app.workers.reputation_tasks.sync_reviews_all_profiles",
        "schedule": 900,
        "options": {"queue": "maintenance"},
    },
    "refresh-google-tokens-10-min": {
        "task": "app.workers.reputation_tasks.refresh_google_tokens",
        "schedule": 600,
        "options": {"queue": "maintenance"},
    },
}
