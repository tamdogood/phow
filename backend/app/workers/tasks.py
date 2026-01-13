from typing import List, Dict, Any
from .celery_app import celery_app
from ..services.location_service import LocationService


@celery_app.task(name="analyze_location_batch")
def analyze_location_batch(addresses: List[str], business_type: str) -> List[Dict[str, Any]]:
    """
    Background task to analyze multiple locations in batch.

    Usage:
        from app.workers import analyze_location_batch
        result = analyze_location_batch.delay(
            ["123 Main St, Austin TX", "456 Oak Ave, Seattle WA"],
            "coffee shop"
        )
        # Get result: result.get()
    """
    import asyncio

    location_service = LocationService()
    results = []

    async def analyze_all():
        for address in addresses:
            try:
                data = await location_service.analyze_location(address, business_type)
                results.append({"address": address, "data": data, "success": True})
            except Exception as e:
                results.append({"address": address, "error": str(e), "success": False})

    # Run async code in celery worker
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(analyze_all())
    loop.close()

    return results


@celery_app.task(name="generate_market_report")
def generate_market_report(location: str, business_type: str) -> Dict[str, Any]:
    """
    Future task: Generate comprehensive market research report.
    This is a placeholder for when you add the Market Research tool.
    """
    # TODO: Implement when Market Research tool is added
    return {
        "location": location,
        "business_type": business_type,
        "status": "not_implemented",
    }
