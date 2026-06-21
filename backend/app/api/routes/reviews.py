"""Reputation Hub endpoints: connect Google, sync, inbox, draft, publish, analytics."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ..deps import get_reputation_service
from ...core.config import get_settings
from ...core.logging import get_logger
from ...services.reputation_service import ReputationService

router = APIRouter(prefix="/reviews", tags=["reviews"])
logger = get_logger("reviews_route")


class ConnectRequest(BaseModel):
    business_profile_id: str


class SyncRequest(BaseModel):
    business_profile_id: str


class PublishRequest(BaseModel):
    text: str


class ManualReviewRequest(BaseModel):
    business_profile_id: str
    review_text: str
    author_name: str | None = None
    rating: int | None = None


@router.post("/connect/google/start")
async def connect_start(
    req: ConnectRequest, service: ReputationService = Depends(get_reputation_service)
):
    """Return the Google OAuth consent URL for the browser to redirect to."""
    try:
        return {"authorization_url": service.build_auth_url(req.business_profile_id)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/connect/google/callback")
async def connect_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    service: ReputationService = Depends(get_reputation_service),
):
    """OAuth redirect target: store tokens, then bounce back to the frontend Hub."""
    frontend = get_settings().frontend_url
    if error or not code or not state:
        return RedirectResponse(f"{frontend}/reviews?error={error or 'missing_code'}")
    try:
        result = await service.complete_connection(code, state)
        return RedirectResponse(
            f"{frontend}/reviews?bid={result['business_profile_id']}&connected=google"
        )
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        return RedirectResponse(f"{frontend}/reviews?error=connect_failed")


@router.get("/connections")
async def list_connections(
    business_profile_id: str, service: ReputationService = Depends(get_reputation_service)
):
    return {"connections": await service.list_connections(business_profile_id)}


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: str, service: ReputationService = Depends(get_reputation_service)
):
    if not await service.connections.delete(connection_id):
        raise HTTPException(status_code=404, detail="Connection not found")
    return {"deleted": True}


@router.post("/sync")
async def sync(req: SyncRequest, service: ReputationService = Depends(get_reputation_service)):
    return await service.sync_reviews(req.business_profile_id)


@router.get("/inbox")
async def inbox(
    business_profile_id: str,
    filter: str = "all",
    source: str | None = None,
    limit: int = 100,
    service: ReputationService = Depends(get_reputation_service),
):
    reviews = await service.reviews.get_inbox(business_profile_id, filter, source, limit)
    return {"reviews": reviews}


@router.post("/{review_id}/draft")
async def draft(review_id: str, service: ReputationService = Depends(get_reputation_service)):
    try:
        return await service.generate_drafts(review_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{review_id}/publish")
async def publish(
    review_id: str,
    req: PublishRequest,
    service: ReputationService = Depends(get_reputation_service),
):
    try:
        return await service.publish_reply(review_id, req.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to publish reply: {e}")


@router.get("/analytics/summary")
async def analytics(
    business_profile_id: str, service: ReputationService = Depends(get_reputation_service)
):
    return await service.get_analytics(business_profile_id)


@router.post("/manual")
async def manual_review(
    req: ManualReviewRequest, service: ReputationService = Depends(get_reputation_service)
):
    """Add a review by hand (universal fallback / works before Google access is approved)."""
    return await service.add_manual_review(
        req.business_profile_id, req.author_name, req.rating, req.review_text
    )
