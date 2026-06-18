from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...core import plans
from ...services.entitlement_service import EntitlementService, EntitlementError

router = APIRouter(prefix="/account", tags=["account"])


class SetPlanRequest(BaseModel):
    business_profile_id: str
    plan: str


def get_entitlement_service(db: Client = Depends(get_supabase)) -> EntitlementService:
    return EntitlementService(db)


@router.get("/plans")
async def list_plans():
    """Public pricing-page data."""
    return {"plans": plans.public_plans()}


@router.get("/entitlements")
async def get_entitlements(
    business_profile_id: str,
    service: EntitlementService = Depends(get_entitlement_service),
):
    return await service.get_entitlements(business_profile_id)


@router.put("/plan")
async def set_plan(
    request: SetPlanRequest,
    service: EntitlementService = Depends(get_entitlement_service),
):
    """Set the active plan. MVP: direct switch; production gates this behind a billing webhook."""
    try:
        return await service.set_plan(request.business_profile_id, request.plan)
    except EntitlementError as e:
        raise HTTPException(status_code=402, detail=str(e))
