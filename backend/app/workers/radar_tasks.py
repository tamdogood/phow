"""Celery tasks for Business Radar: per-scan execution + the due-scan dispatcher."""

from typing import Any
from .celery_app import celery_app
from .tasks import run_async
from ..core.logging import get_logger
from ..api.deps import get_supabase

logger = get_logger("radar_tasks")


@celery_app.task(bind=True, max_retries=1, time_limit=900)
def run_radar_scan(self, subscription_id: str) -> dict[str, Any]:
    """Run one radar scan. ``RadarService.run_scan`` manages status/errors itself."""
    logger.info("Starting radar scan", subscription_id=subscription_id)

    async def _run():
        from ..services.radar_service import RadarService

        await RadarService(get_supabase()).run_scan(subscription_id)

    run_async(_run())
    return {"subscription_id": subscription_id}


@celery_app.task
def dispatch_due_radar_scans() -> dict[str, Any]:
    """Beat task: dispatch a scan for every active subscription that is due.

    This is the per-entity scheduler the codebase previously lacked (beat was
    global-cron only).
    """

    async def _due():
        from ..services.radar_service import RadarService

        return await RadarService(get_supabase()).get_due_subscription_ids()

    due = run_async(_due())
    for subscription_id in due:
        run_radar_scan.delay(subscription_id)
    logger.info("Dispatched due radar scans", count=len(due))
    return {"dispatched": len(due)}
