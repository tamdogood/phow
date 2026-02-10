from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..deps import get_supabase
from ...services.business_profile_service import BusinessProfileService
from ...services.analysis_service import AnalysisService
from ...services.demographics_service import get_demographics_service
from ...repositories.conversation_repository import ConversationRepository
from ...core.logging import get_logger

logger = get_logger("dashboard")
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_business_profile_service(db: Client = Depends(get_supabase)) -> BusinessProfileService:
    return BusinessProfileService(db)


def get_conversation_repo(db: Client = Depends(get_supabase)) -> ConversationRepository:
    return ConversationRepository(db)


def get_analysis_service(db: Client = Depends(get_supabase)) -> AnalysisService:
    return AnalysisService(db)


@router.get("")
async def get_dashboard(
    session_id: str | None = None,
    user_id: str | None = None,
    service: BusinessProfileService = Depends(get_business_profile_service),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Get aggregated dashboard data for a user or session."""
    if not session_id and not user_id:
        raise HTTPException(status_code=400, detail="session_id or user_id required")

    # Get business profile
    profile = None
    if user_id:
        profile = await service.get_profile_by_user(user_id)
    if not profile and session_id:
        profile = await service.get_profile(session_id)

    if not profile:
        return {
            "has_profile": False,
            "business_profile": None,
            "market_analysis": None,
            "competitor_analysis": None,
            "tracked_competitors": [],
            "recent_conversations": [],
            "demographics": None,
        }

    profile_id = profile["id"]

    # Get related data
    market_analysis = await service.get_latest_market_analysis(profile_id)
    competitor_analysis = await service.get_latest_competitor_analysis(profile_id)
    tracked_competitors = await service.get_competitors(profile_id)

    # Get recent conversations
    conversations = []
    if session_id:
        conversations = await conversation_repo.get_by_session(session_id, limit=10)

    # Get demographics if location address exists
    demographics_data = None
    address = profile.get("location_address")
    if address:
        try:
            demographics_service = get_demographics_service()
            result = await demographics_service.get_demographics_for_address(address)
            if result.get("error"):
                logger.warning("Demographics fetch error", address=address, error=result.get("error"))
            elif result.get("demographics"):
                business_type = profile.get("business_type", "")
                demographics_data = {
                    "demographics": result["demographics"],
                    "summary": await demographics_service.get_demographics_summary(result["demographics"]),
                    "fit_analysis": demographics_service.calculate_demographic_fit_score(
                        result["demographics"], business_type
                    ) if business_type else None,
                }
        except Exception as e:
            logger.error("Demographics exception", address=address, error=str(e))
            pass  # Demographics are optional, don't fail the dashboard

    return {
        "has_profile": True,
        "business_profile": profile,
        "market_analysis": market_analysis,
        "competitor_analysis": competitor_analysis,
        "tracked_competitors": tracked_competitors,
        "recent_conversations": conversations,
        "demographics": demographics_data,
    }


@router.post("/analyze")
async def trigger_analysis(
    session_id: str | None = None,
    user_id: str | None = None,
    analysis_service: AnalysisService = Depends(get_analysis_service),
    profile_service: BusinessProfileService = Depends(get_business_profile_service),
    conversation_repo: ConversationRepository = Depends(get_conversation_repo),
):
    """Trigger auto-analysis for dashboard metrics and return updated data."""
    if not session_id and not user_id:
        raise HTTPException(status_code=400, detail="session_id or user_id required")

    # Run analysis if needed
    analysis_result = await analysis_service.analyze_if_needed(session_id, user_id)

    if "error" in analysis_result and analysis_result.get("error") == "No business profile found":
        raise HTTPException(status_code=404, detail="Business profile not found")

    # Return updated dashboard data
    profile = None
    if user_id:
        profile = await profile_service.get_profile_by_user(user_id)
    if not profile and session_id:
        profile = await profile_service.get_profile(session_id)

    if not profile:
        return {"has_profile": False, "analyzed": False}

    profile_id = profile["id"]

    market_analysis = await profile_service.get_latest_market_analysis(profile_id)
    competitor_analysis = await profile_service.get_latest_competitor_analysis(profile_id)
    tracked_competitors = await profile_service.get_competitors(profile_id)

    conversations = []
    if session_id:
        conversations = await conversation_repo.get_by_session(session_id, limit=10)

    # Get demographics if location address exists
    demographics_data = None
    address = profile.get("location_address")
    if address:
        try:
            demographics_service = get_demographics_service()
            result = await demographics_service.get_demographics_for_address(address)
            if result.get("error"):
                logger.warning("Demographics fetch error", address=address, error=result.get("error"))
            elif result.get("demographics"):
                business_type = profile.get("business_type", "")
                demographics_data = {
                    "demographics": result["demographics"],
                    "summary": await demographics_service.get_demographics_summary(result["demographics"]),
                    "fit_analysis": demographics_service.calculate_demographic_fit_score(
                        result["demographics"], business_type
                    ) if business_type else None,
                }
        except Exception as e:
            logger.error("Demographics exception", address=address, error=str(e))
            pass

    return {
        "has_profile": True,
        "analyzed": analysis_result.get("analyzed", False),
        "business_profile": profile,
        "market_analysis": market_analysis,
        "competitor_analysis": competitor_analysis,
        "tracked_competitors": tracked_competitors,
        "recent_conversations": conversations,
        "demographics": demographics_data,
    }


@router.get("/demographics")
async def get_demographics(
    address: str,
    business_type: str | None = None,
):
    """
    Get comprehensive demographic data for an address.

    Returns Census data including:
    - Population & density
    - Income distribution
    - Age breakdown
    - Education levels
    - Race/ethnicity
    - Household composition
    - Employment & industry
    - Commute patterns
    """
    if not address:
        raise HTTPException(status_code=400, detail="address is required")

    demographics_service = get_demographics_service()
    result = await demographics_service.get_demographics_for_address(address)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    response = {
        "demographics": result["demographics"],
        "summary": await demographics_service.get_demographics_summary(result["demographics"]),
    }

    # Add demographic fit score if business type provided
    if business_type:
        response["fit_analysis"] = demographics_service.calculate_demographic_fit_score(
            result["demographics"], business_type
        )

    return response


@router.get("/demographics/profile")
async def get_demographics_for_profile(
    session_id: str | None = None,
    user_id: str | None = None,
    service: BusinessProfileService = Depends(get_business_profile_service),
):
    """Get demographics for the user's business profile location."""
    if not session_id and not user_id:
        raise HTTPException(status_code=400, detail="session_id or user_id required")

    # Get business profile
    profile = None
    if user_id:
        profile = await service.get_profile_by_user(user_id)
    if not profile and session_id:
        profile = await service.get_profile(session_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    address = profile.get("location_address")
    if not address:
        raise HTTPException(status_code=400, detail="Business profile has no location address")

    business_type = profile.get("business_type", "")

    demographics_service = get_demographics_service()
    result = await demographics_service.get_demographics_for_address(address)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return {
        "demographics": result["demographics"],
        "summary": await demographics_service.get_demographics_summary(result["demographics"]),
        "fit_analysis": demographics_service.calculate_demographic_fit_score(
            result["demographics"], business_type
        ),
        "business_profile": {
            "name": profile.get("business_name"),
            "type": business_type,
            "address": address,
        },
    }
