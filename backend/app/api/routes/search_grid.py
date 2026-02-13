from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...services.search_grid_service import SearchGridService

router = APIRouter(prefix="/search-grid", tags=["search-grid"])


def get_search_grid_service(db: Client = Depends(get_supabase)) -> SearchGridService:
    return SearchGridService(db)


class CreateReportRequest(BaseModel):
    business_profile_id: str
    name: str
    keywords: list[str]
    radius_km: float = 5
    grid_size: int = 7
    frequency: str = "weekly"
    schedule_day: int = 5
    schedule_hour: int = 9
    timezone: str = "America/New_York"
    notify_email: str | None = None


class UpdateReportRequest(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
    radius_km: float | None = None
    grid_size: int | None = None
    frequency: str | None = None
    schedule_day: int | None = None
    schedule_hour: int | None = None
    timezone: str | None = None
    notify_email: str | None = None


@router.post("/reports")
async def create_report(
    request: CreateReportRequest,
    service: SearchGridService = Depends(get_search_grid_service),
):
    try:
        report = await service.create_report(
            business_profile_id=request.business_profile_id,
            name=request.name,
            keywords=request.keywords,
            radius_km=request.radius_km,
            grid_size=request.grid_size,
            frequency=request.frequency,
            schedule_day=request.schedule_day,
            schedule_hour=request.schedule_hour,
            timezone=request.timezone,
            notify_email=request.notify_email,
        )
        return {"report": report}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports")
async def list_reports(
    profile_id: str,
    service: SearchGridService = Depends(get_search_grid_service),
):
    reports = await service.list_reports_summary(profile_id)
    return {"reports": reports}


@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    service: SearchGridService = Depends(get_search_grid_service),
):
    report = await service.get_report_with_results(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report": report}


@router.put("/reports/{report_id}")
async def update_report(
    report_id: str,
    request: UpdateReportRequest,
    service: SearchGridService = Depends(get_search_grid_service),
):
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    report = await service.update_report(report_id, updates)
    return {"report": report}


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    service: SearchGridService = Depends(get_search_grid_service),
):
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"deleted": True}


@router.post("/reports/{report_id}/run")
async def trigger_run(
    report_id: str,
    service: SearchGridService = Depends(get_search_grid_service),
):
    try:
        result = await service.trigger_run(report_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs/{run_id}/results")
async def get_run_results(
    run_id: str,
    keyword: str | None = None,
    service: SearchGridService = Depends(get_search_grid_service),
):
    results = await service.get_run_results(run_id, keyword)
    return {"results": results}
