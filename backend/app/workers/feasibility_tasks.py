"""Celery task for feasibility study generation."""

from typing import Any
from .celery_app import celery_app
from .tasks import run_async
from ..core.logging import get_logger
from ..api.deps import get_supabase

logger = get_logger("feasibility_tasks")


@celery_app.task(bind=True, max_retries=1, time_limit=900)
def run_feasibility_report(self, report_id: str) -> dict[str, Any]:
    """Run the deterministic feasibility pipeline for one report.

    ``FeasibilityService.run_pipeline`` updates row status/progress and marks
    failures itself, so this wrapper stays thin and does not re-raise.
    """
    logger.info("Starting feasibility report", report_id=report_id)

    async def _run():
        from ..services.feasibility_service import FeasibilityService

        service = FeasibilityService(get_supabase())
        await service.run_pipeline(report_id)

    run_async(_run())
    return {"report_id": report_id}
