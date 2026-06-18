"""Celery tasks for the Daily Brief: per-business generation + morning dispatcher."""

from typing import Any
from .celery_app import celery_app
from .tasks import run_async
from ..core.logging import get_logger
from ..api.deps import get_supabase

logger = get_logger("daily_brief_tasks")


@celery_app.task(bind=True, max_retries=1, time_limit=300)
def generate_daily_brief(self, business_profile_id: str) -> dict[str, Any]:
    """Generate (or refresh) today's brief for one business."""
    logger.info("Generating daily brief", business_profile_id=business_profile_id)

    async def _run():
        from ..services.daily_brief_service import DailyBriefService

        await DailyBriefService(get_supabase()).generate(business_profile_id)

    run_async(_run())
    return {"business_profile_id": business_profile_id}


@celery_app.task
def dispatch_due_daily_briefs() -> dict[str, Any]:
    """Beat task: generate today's brief for every active business that lacks one."""

    async def _due():
        from ..services.daily_brief_service import DailyBriefService

        return await DailyBriefService(get_supabase()).get_due_profile_ids()

    due = run_async(_due())
    for business_profile_id in due:
        generate_daily_brief.delay(business_profile_id)
    logger.info("Dispatched due daily briefs", count=len(due))
    return {"dispatched": len(due)}
