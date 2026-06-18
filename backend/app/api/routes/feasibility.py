from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..deps import get_supabase
from ...models.feasibility import CreateFeasibilityRequest
from ...services.feasibility_service import FeasibilityService

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


def get_feasibility_service(db: Client = Depends(get_supabase)) -> FeasibilityService:
    return FeasibilityService(db)


@router.post("/reports")
async def create_report(
    request: CreateFeasibilityRequest,
    service: FeasibilityService = Depends(get_feasibility_service),
):
    report = await service.create_report(
        session_id=request.session_id,
        concept=request.concept,
        location_address=request.location_address,
        user_id=request.user_id,
        business_profile_id=request.business_profile_id,
        scale_seats=request.scale_seats,
        startup_budget=request.startup_budget,
    )
    return {"report": report}


@router.get("/reports")
async def list_reports(
    session_id: str | None = None,
    user_id: str | None = None,
    service: FeasibilityService = Depends(get_feasibility_service),
):
    reports = await service.list_reports(session_id=session_id, user_id=user_id)
    return {"reports": reports}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    service: FeasibilityService = Depends(get_feasibility_service),
):
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report": report}


@router.post("/reports/{report_id}/rerun")
async def rerun_report(
    report_id: str,
    service: FeasibilityService = Depends(get_feasibility_service),
):
    try:
        return await service.rerun(report_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    service: FeasibilityService = Depends(get_feasibility_service),
):
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"deleted": True}
