"""Review response draft and publish workflow service."""

from __future__ import annotations

from supabase import Client

from ..core.config import get_settings
from ..repositories.reviews_repository import (
    ReviewResponseRepository,
    ReviewRepository,
    ReviewActivityLogRepository,
)
from .review_usage_service import ReviewUsageService
from .review_errors import (
    ValidationFailedError,
    IdempotencyConflictError,
    PolicyBlockedError,
    ProviderUnavailableError,
)

VALID_TONES = {"professional", "friendly", "apologetic"}


class ReviewResponseService:
    """Generates draft responses and publishes approved responses."""

    def __init__(self, db: Client):
        self.settings = get_settings()
        self.response_repo = ReviewResponseRepository(db)
        self.review_repo = ReviewRepository(db)
        self.activity_repo = ReviewActivityLogRepository(db)
        self.usage_service = ReviewUsageService(db)

    def _guardrail_check(self, text: str):
        blocked_tokens = ["hate", "racist", "sexist", "violent"]
        lowered = text.lower()
        if any(token in lowered for token in blocked_tokens):
            raise PolicyBlockedError("Draft contains unsafe language")

    def _draft_template(self, tone: str, review: dict) -> str:
        reviewer = review.get("reviewer_name") or "there"
        content = (review.get("content") or "").strip()
        rating = int(review.get("rating") or 0)

        if tone == "professional":
            return (
                f"Hi {reviewer}, thank you for sharing your feedback. "
                f"We appreciate your {rating}-star review and will use your comments to improve. "
                f"{('Your note: ' + content[:160]) if content else ''}".strip()
            )
        if tone == "friendly":
            return (
                f"Hey {reviewer}, thanks a lot for taking the time to leave a review! "
                f"We are glad you reached out and we value your {rating}-star feedback. "
                f"{('We hear you: ' + content[:160]) if content else ''}".strip()
            )
        if tone == "apologetic":
            return (
                f"Hi {reviewer}, we are sorry your experience did not meet expectations. "
                "Thank you for the honest feedback, and we are addressing this with our team immediately. "
                f"{('We noted: ' + content[:160]) if content else ''}".strip()
            )
        raise ValidationFailedError(f"Unsupported tone '{tone}'")

    async def generate_drafts(
        self,
        *,
        business_profile_id: str,
        review: dict,
        actor_session_id: str | None,
        actor_user_id: str | None,
        plan: str | None,
    ) -> list[dict]:
        await self.usage_service.ensure_can_generate(business_profile_id, plan)

        drafts = []
        for tone in ["professional", "friendly", "apologetic"]:
            draft_text = self._draft_template(tone, review)
            self._guardrail_check(draft_text)
            drafts.append(
                await self.response_repo.create(
                    review_id=review["id"],
                    tone=tone,
                    draft_text=draft_text,
                )
            )

        await self.activity_repo.log(
            business_profile_id=business_profile_id,
            review_id=review["id"],
            source=review.get("source"),
            action="draft_generated",
            actor_session_id=actor_session_id,
            actor_user_id=actor_user_id,
            details={"count": len(drafts)},
        )

        return drafts

    async def publish(
        self,
        *,
        business_profile_id: str,
        review: dict,
        response_text: str,
        tone: str,
        idempotency_key: str,
        actor_session_id: str | None,
        actor_user_id: str | None,
    ) -> dict:
        if not idempotency_key:
            raise ValidationFailedError("idempotency_key is required")
        if tone not in VALID_TONES:
            raise ValidationFailedError(f"Unsupported tone '{tone}'")

        self._guardrail_check(response_text)

        existing = await self.response_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            raise IdempotencyConflictError()

        created = await self.response_repo.create(
            review_id=review["id"],
            tone=tone,
            draft_text=response_text,
            edited_text=response_text,
            status="draft",
            idempotency_key=idempotency_key,
        )

        provider_result = await self._publish_to_provider(review["source"], response_text)

        published = await self.response_repo.mark_published(
            created["id"],
            final_text=response_text,
            provider_response=provider_result,
        )

        await self.review_repo.mark_replied(review["id"])

        await self.activity_repo.log(
            business_profile_id=business_profile_id,
            review_id=review["id"],
            source=review.get("source"),
            action="response_published",
            actor_session_id=actor_session_id,
            actor_user_id=actor_user_id,
            details={"tone": tone, "idempotency_key": idempotency_key},
        )

        return published or created

    async def _publish_to_provider(self, source: str, response_text: str) -> dict:
        if source == "yelp":
            return {
                "mode": "deeplink",
                "url": "https://biz.yelp.com",
                "status": "manual_action_required",
            }

        if source == "google":
            if not self.settings.reputation_live_connectors_enabled:
                raise ProviderUnavailableError("Live connector publishing is disabled")
            # Placeholder for Google publish endpoint integration.
            return {
                "mode": "api",
                "status": "accepted",
                "provider": "google",
                "preview": response_text[:120],
            }

        raise ProviderUnavailableError(f"Publishing is unavailable for source '{source}'")
