from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..deps import get_supabase
from ...models.radar import RadarScanRequest, RadarSubscriptionUpdate
from ...services.radar_service import RadarService

router = APIRouter(prefix="/radar", tags=["radar"])


def get_radar_service(db: Client = Depends(get_supabase)) -> RadarService:
    return RadarService(db)


@router.get("/feed")
async def get_feed(
    business_profile_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    service: RadarService = Depends(get_radar_service),
):
    return await service.get_feed(business_profile_id, status, limit, offset)


@router.get("/subscription")
async def get_subscription(
    business_profile_id: str,
    service: RadarService = Depends(get_radar_service),
):
    try:
        sub = await service.get_or_create_for_profile(business_profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"subscription": sub}


@router.put("/subscription")
async def update_subscription(
    request: RadarSubscriptionUpdate,
    service: RadarService = Depends(get_radar_service),
):
    fields = request.model_dump(exclude={"business_profile_id"}, exclude_none=True)
    try:
        sub = await service.update_subscription(request.business_profile_id, fields)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"subscription": sub}


@router.post("/scan")
async def trigger_scan(
    request: RadarScanRequest,
    service: RadarService = Depends(get_radar_service),
):
    try:
        return await service.trigger_scan(request.business_profile_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/alerts/{alert_id}/read")
async def mark_read(alert_id: str, service: RadarService = Depends(get_radar_service)):
    res = await service.mark_alert(alert_id, "read")
    if not res:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": res}


@router.post("/alerts/{alert_id}/dismiss")
async def mark_dismiss(alert_id: str, service: RadarService = Depends(get_radar_service)):
    res = await service.mark_alert(alert_id, "dismissed")
    if not res:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": res}
