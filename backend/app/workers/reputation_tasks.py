"""Celery tasks for the Reputation Hub: scheduled review syncing."""

from typing import Any

from .celery_app import celery_app
from .tasks import run_async
from ..api.deps import get_supabase
from ..core.logging import get_logger
from ..services.reputation_service import ReputationService

logger = get_logger("reputation_tasks")


@celery_app.task
def sync_all_reviews() -> dict[str, Any]:
    """Sync reviews for every connected Google Business Profile (beat: every 15 min)."""
    service = ReputationService(get_supabase())

    async def _run():
        connections = await service.connections.list_all_connected()
        results = []
        for conn in connections:
            res = await service.sync_reviews(conn["business_profile_id"])
            results.append({"business_profile_id": conn["business_profile_id"], **res})
        return {"connections": len(connections), "results": results}

    result = run_async(_run())
    logger.info("sync_all_reviews complete", connections=result["connections"])
    return result
