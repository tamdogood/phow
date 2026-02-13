"""Reputation Hub API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from supabase import Client

from ..deps import get_supabase
from ...repositories.reviews_repository import ReviewRepository, ReviewSentimentRepository
from ...services.review_authz_service import ReviewAuthzService
from ...services.connection_service import ConnectionService
from ...services.review_ingestion_service import ReviewIngestionService
from ...services.review_response_service import ReviewResponseService
from ...services.review_analytics_service import ReviewAnalyticsService
from ...services.review_notification_service import ReviewNotificationService
from ...services.review_usage_service import ReviewUsageService
from ...services.review_errors import ReviewServiceError

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _raise_review_error(exc: ReviewServiceError):
    raise HTTPException(
        status_code=exc.status_code,
        detail={"error": {"code": exc.code, "message": exc.message}},
    )


def _internal_error(exc: Exception):
    raise HTTPException(
        status_code=500,
        detail={
            "error": {
                "code": "provider_unavailable",
                "message": str(exc),
            }
        },
    )


class ActorRequest(BaseModel):
    session_id: str | None = None
    user_id: str | None = None


class ConnectionCallbackRequest(ActorRequest):
    code: str
    state: str | None = None


class SyncRequest(ActorRequest):
    source: str | None = Field(default=None, pattern="^(google|yelp|meta)$")
    mode: str = Field(default="manual", pattern="^(manual|scheduled)$")


class PublishRequest(ActorRequest):
    response_text: str
    tone: str = Field(pattern="^(professional|friendly|apologetic)$")
    idempotency_key: str


class DraftRequest(ActorRequest):
    plan: str | None = None


class AlertSettingsRequest(ActorRequest):
    low_rating_threshold: int = Field(ge=1, le=5)
    instant_low_rating_enabled: bool = True
    daily_digest_enabled: bool = False


@router.get("/health")
async def health():
    return {"status": "ok", "service": "reputation_hub"}


@router.get("/connections")
async def get_connections(
    session_id: str | None = None,
    user_id: str | None = None,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        items = await ConnectionService(db).list_connections(profile["id"])
        return {"connections": items}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/connections/{source}/start")
async def start_connection(
    source: str,
    request: ActorRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        result = await ConnectionService(db).start_connection(
            business_profile_id=profile["id"],
            source=source,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
        )
        return result
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/connections/{source}/callback")
async def callback_connection(
    source: str,
    request: ConnectionCallbackRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        result = await ConnectionService(db).callback_connection(
            business_profile_id=profile["id"],
            source=source,
            code=request.code,
            state=request.state,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
        )
        return result
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.delete("/connections/{source}")
async def delete_connection(
    source: str,
    request: ActorRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        result = await ConnectionService(db).disconnect(
            business_profile_id=profile["id"],
            source=source,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
        )
        return result
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/sync")
async def sync_reviews(
    request: SyncRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        result = await ReviewIngestionService(db).sync(
            business_profile_id=profile["id"],
            source=request.source,
            mode=request.mode,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
        )
        return result
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/inbox")
async def get_inbox(
    session_id: str | None = None,
    user_id: str | None = None,
    source: str | None = Query(default=None),
    sentiment: str | None = Query(default=None, pattern="^(positive|neutral|negative)$"),
    unreplied_only: bool = False,
    min_rating: int | None = Query(default=None, ge=1, le=5),
    max_rating: int | None = Query(default=None, ge=1, le=5),
    search: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=session_id, user_id=user_id)

        review_repo = ReviewRepository(db)
        sentiment_repo = ReviewSentimentRepository(db)

        reviews = await review_repo.list_inbox(
            profile["id"],
            source=source,
            unreplied_only=unreplied_only,
            min_rating=min_rating,
            max_rating=max_rating,
            search=search,
            cursor=cursor,
            limit=limit,
        )

        sentiments = await sentiment_repo.list_by_review_ids([review["id"] for review in reviews])
        sentiment_map = {row["review_id"]: row for row in sentiments}

        enriched = []
        for review in reviews:
            row = {
                **review,
                "sentiment": sentiment_map.get(review["id"]),
            }
            if sentiment and (row["sentiment"] or {}).get("sentiment_label") != sentiment:
                continue
            enriched.append(row)

        next_cursor = enriched[-1]["review_created_at"] if enriched else None

        return {
            "items": enriched,
            "next_cursor": next_cursor,
        }
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/{review_id}/draft")
async def generate_draft(
    review_id: str,
    request: DraftRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        review = await authz.get_review_for_profile(review_id, profile["id"])
        drafts = await ReviewResponseService(db).generate_drafts(
            business_profile_id=profile["id"],
            review=review,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
            plan=request.plan,
        )
        return {"drafts": drafts}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/{review_id}/publish")
async def publish_response(
    review_id: str,
    request: PublishRequest,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=request.session_id, user_id=request.user_id)
        review = await authz.get_review_for_profile(review_id, profile["id"])
        published = await ReviewResponseService(db).publish(
            business_profile_id=profile["id"],
            review=review,
            response_text=request.response_text,
            tone=request.tone,
            idempotency_key=request.idempotency_key,
            actor_session_id=request.session_id,
            actor_user_id=request.user_id,
        )
        return {"response": published}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/analytics/summary")
async def analytics_summary(
    session_id: str | None = None,
    user_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewAnalyticsService(db).summary(profile["id"], days=days)
        return data
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/analytics/trends")
async def analytics_trends(
    session_id: str | None = None,
    user_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewAnalyticsService(db).trends(profile["id"], days=days)
        return {"points": data}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/analytics/themes")
async def analytics_themes(
    session_id: str | None = None,
    user_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewAnalyticsService(db).themes(profile["id"], days=days)
        return {"themes": data}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/analytics/platforms")
async def analytics_platforms(
    session_id: str | None = None,
    user_id: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewAnalyticsService(db).platforms(profile["id"], days=days)
        return {"platforms": data}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/competitors")
async def competitors(
    session_id: str | None = None,
    user_id: str | None = None,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewAnalyticsService(db).competitors(profile["id"])
        return {"items": data}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/notifications")
async def get_notifications(
    session_id: str | None = None,
    user_id: str | None = None,
    unread_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewNotificationService(db).list_notifications(
            profile["id"],
            unread_only=unread_only,
            limit=limit,
        )
        return data
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    request: ActorRequest,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(
            session_id=request.session_id,
            user_id=request.user_id,
        )
        updated = await ReviewNotificationService(db).mark_read(profile["id"], notification_id)
        if not updated:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "validation_failed", "message": "Notification not found"}},
            )
        return {"updated": True}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.post("/notifications/read-all")
async def mark_notifications_read_all(
    request: ActorRequest,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(
            session_id=request.session_id,
            user_id=request.user_id,
        )
        count = await ReviewNotificationService(db).mark_all_read(profile["id"])
        return {"updated_count": count}
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/alerts/settings")
async def get_alert_settings(
    session_id: str | None = None,
    user_id: str | None = None,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        data = await ReviewNotificationService(db).get_alert_settings(profile["id"])
        return data
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.put("/alerts/settings")
async def update_alert_settings(
    request: AlertSettingsRequest,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(
            session_id=request.session_id,
            user_id=request.user_id,
        )
        data = await ReviewNotificationService(db).update_alert_settings(
            business_profile_id=profile["id"],
            low_rating_threshold=request.low_rating_threshold,
            instant_low_rating_enabled=request.instant_low_rating_enabled,
            daily_digest_enabled=request.daily_digest_enabled,
        )
        return data
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/usage")
async def usage(
    session_id: str | None = None,
    user_id: str | None = None,
    plan: str | None = None,
    db: Client = Depends(get_supabase),
):
    try:
        profile = await ReviewAuthzService(db).resolve_profile(session_id=session_id, user_id=user_id)
        usage_data = await ReviewUsageService(db).get_usage(profile["id"], plan)
        return usage_data
    except ReviewServiceError as exc:
        _raise_review_error(exc)


@router.get("/{review_id}")
async def get_review_detail(
    review_id: str,
    session_id: str | None = None,
    user_id: str | None = None,
    db: Client = Depends(get_supabase),
):
    try:
        authz = ReviewAuthzService(db)
        profile = await authz.resolve_profile(session_id=session_id, user_id=user_id)
        review = await authz.get_review_for_profile(review_id, profile["id"])

        sentiments = await ReviewSentimentRepository(db).list_by_review_ids([review_id])

        return {
            "review": review,
            "sentiment": sentiments[0] if sentiments else None,
        }
    except ReviewServiceError as exc:
        _raise_review_error(exc)
    except Exception as exc:
        _internal_error(exc)
