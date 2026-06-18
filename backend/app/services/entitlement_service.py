"""Resolves a business's plan and enforces tier limits/features."""

from typing import Any

from supabase import Client

from ..core import plans
from ..repositories.business_profile_repository import (
    BusinessProfileRepository,
    TrackedCompetitorRepository,
)


class EntitlementError(Exception):
    """Raised when an action is not permitted on the current plan (maps to HTTP 402)."""

    def __init__(self, message: str, plan: str, upgrade_to: str = "pro"):
        super().__init__(message)
        self.plan = plan
        self.upgrade_to = upgrade_to


class EntitlementService:
    def __init__(self, db: Client):
        self.db = db
        self.profile_repo = BusinessProfileRepository(db)
        self.competitor_repo = TrackedCompetitorRepository(db)

    async def get_plan_name(self, business_profile_id: str) -> str:
        profile = await self.profile_repo.get_by_id(business_profile_id)
        return plans.plan_name((profile or {}).get("plan"))

    async def get_entitlements(self, business_profile_id: str) -> dict[str, Any]:
        name = await self.get_plan_name(business_profile_id)
        ent = plans.entitlements(name)
        # Live usage so the UI can show "3 of 15 competitors".
        used = len(await self.competitor_repo.get_competitors(business_profile_id))
        ent["usage"] = {
            "tracked_competitors": used,
            "tracked_competitors_remaining": plans.remaining(name, "tracked_competitors", used),
        }
        return ent

    async def set_plan(self, business_profile_id: str, plan: str) -> dict[str, Any]:
        await self.profile_repo.update(business_profile_id, plan=plans.plan_name(plan))
        return await self.get_entitlements(business_profile_id)

    async def require_feature(self, business_profile_id: str, feature: str) -> None:
        name = await self.get_plan_name(business_profile_id)
        if not plans.has_feature(name, feature):
            raise EntitlementError(
                f"{feature.replace('_', ' ').title()} requires an upgrade.", name
            )

    async def require_capacity(self, business_profile_id: str, key: str, used: int) -> None:
        name = await self.get_plan_name(business_profile_id)
        if not plans.within_limit(name, key, used):
            cap = plans.limit(name, key)
            raise EntitlementError(
                f"You've reached your plan limit of {cap} for {key.replace('_', ' ')}.", name
            )
