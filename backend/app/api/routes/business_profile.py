from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..deps import get_supabase
from ...services.business_profile_service import BusinessProfileService

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
