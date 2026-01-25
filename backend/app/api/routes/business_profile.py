import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...services.business_profile_service import BusinessProfileService
from ...repositories.business_profile_repository import TrackedCompetitorRepository

router = APIRouter(prefix="/business-profile", tags=["business-profile"])


class BusinessProfileRequest(BaseModel):
    session_id: str
    user_id: str | None = None
    business_name: str
    business_type: str
    location_address: str
    target_customers: str | None = None
    business_description: str | None = None


def get_business_profile_service(db: Client = Depends(get_supabase)) -> BusinessProfileService:
    return BusinessProfileService(db)


@router.post("")
async def save_profile(
    request: BusinessProfileRequest,
    service: BusinessProfileService = Depends(get_business_profile_service),
):
    """Create or update a business profile."""
    profile = await service.create_or_update_profile(
        session_id=request.session_id,
        business_type=request.business_type,
        business_name=request.business_name,
        business_description=request.business_description,
        target_customers=request.target_customers,
        location_address=request.location_address,
        user_id=request.user_id,
    )
    return {"profile": profile}


@router.get("")
async def get_profile(
    session_id: str | None = None,
    user_id: str | None = None,
    service: BusinessProfileService = Depends(get_business_profile_service),
):
    """Get the business profile by session_id or user_id."""
    if not session_id and not user_id:
        raise HTTPException(status_code=400, detail="session_id or user_id required")

    profile = None
    if user_id:
        profile = await service.get_profile_by_user(user_id)
    if not profile and session_id:
        profile = await service.get_profile(session_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@router.delete("")
async def delete_profile(
    session_id: str,
    service: BusinessProfileService = Depends(get_business_profile_service),
):
    """Delete the business profile for a session."""
    profile = await service.get_profile(session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await service.profile_repo.delete(profile["id"])
    return {"deleted": True}


class AddCompetitorRequest(BaseModel):
    session_id: str
    name: str
    address: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None


class DeleteCompetitorRequest(BaseModel):
    session_id: str


def get_competitor_repo(db: Client = Depends(get_supabase)) -> TrackedCompetitorRepository:
    return TrackedCompetitorRepository(db)


@router.post("/competitors")
async def add_competitor(
    request: AddCompetitorRequest,
    service: BusinessProfileService = Depends(get_business_profile_service),
    competitor_repo: TrackedCompetitorRepository = Depends(get_competitor_repo),
):
    """Add a competitor manually."""
    profile = await service.get_profile(request.session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    # Generate a unique place_id for manually added competitors
    place_id = f"manual-{uuid.uuid4()}"

    competitor = await competitor_repo.add_competitor(
        business_profile_id=profile["id"],
        place_id=place_id,
        name=request.name,
        address=request.address,
        rating=request.rating,
        review_count=request.review_count,
        price_level=request.price_level,
    )
    return {"competitor": competitor}


@router.delete("/competitors/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    request: DeleteCompetitorRequest,
    service: BusinessProfileService = Depends(get_business_profile_service),
    competitor_repo: TrackedCompetitorRepository = Depends(get_competitor_repo),
):
    """Delete a tracked competitor."""
    profile = await service.get_profile(request.session_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    deleted = await competitor_repo.delete_competitor(competitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"deleted": True}
