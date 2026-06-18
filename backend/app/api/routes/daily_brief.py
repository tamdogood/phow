from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..deps import get_supabase
from ...models.daily_brief import DailyBriefGenerateRequest
from ...services.daily_brief_service import DailyBriefService

router = APIRouter(prefix="/daily-brief", tags=["daily-brief"])


def get_daily_brief_service(db: Client = Depends(get_supabase)) -> DailyBriefService:
    return DailyBriefService(db)


@router.get("")
async def get_brief(
    business_profile_id: str,
    service: DailyBriefService = Depends(get_daily_brief_service),
):
    return await service.get_latest(business_profile_id)


@router.post("/generate")
async def generate_brief(
    request: DailyBriefGenerateRequest,
    service: DailyBriefService = Depends(get_daily_brief_service),
):
    try:
        return {"brief": await service.generate(request.business_profile_id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
