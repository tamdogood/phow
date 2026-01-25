from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from ..deps import get_supabase
from ...services.business_profile_service import BusinessProfileService
from ...services.analysis_service import AnalysisService
from ...repositories.conversation_repository import ConversationRepository

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

    return {
        "has_profile": True,
        "business_profile": profile,
        "market_analysis": market_analysis,
        "competitor_analysis": competitor_analysis,
        "tracked_competitors": tracked_competitors,
        "recent_conversations": conversations,
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

    return {
        "has_profile": True,
        "analyzed": analysis_result.get("analyzed", False),
        "business_profile": profile,
        "market_analysis": market_analysis,
        "competitor_analysis": competitor_analysis,
        "tracked_competitors": tracked_competitors,
        "recent_conversations": conversations,
    }
