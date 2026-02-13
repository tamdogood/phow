"""Ownership and profile resolution helpers for Reputation Hub."""

from __future__ import annotations

from supabase import Client

from ..repositories.business_profile_repository import BusinessProfileRepository
from ..repositories.reviews_repository import ReviewRepository
from .review_errors import ValidationFailedError, OwnershipForbiddenError


class ReviewAuthzService:
    """Resolves business profile context and enforces ownership."""

    def __init__(self, db: Client):
        self.profile_repo = BusinessProfileRepository(db)
        self.review_repo = ReviewRepository(db)

    async def resolve_profile(
        self,
        *,
        session_id: str | None,
        user_id: str | None,
    ) -> dict:
        if not session_id and not user_id:
            raise ValidationFailedError("session_id or user_id is required")

        profile = None
        if user_id:
            profile = await self.profile_repo.get_latest_by_user(user_id)
        if not profile and session_id:
            profile = await self.profile_repo.get_latest_by_session(session_id)

        if not profile:
            raise OwnershipForbiddenError("Business profile not found for this identity")

        return profile

    async def get_review_for_profile(self, review_id: str, business_profile_id: str) -> dict:
        review = await self.review_repo.get_by_id_and_profile(review_id, business_profile_id)
        if not review:
            raise OwnershipForbiddenError("Review does not belong to this business")
        return review
