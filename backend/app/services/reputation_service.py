"""Reputation Hub orchestration: connect, sync, draft, publish, analytics."""

import json
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client
from langchain_core.messages import HumanMessage, SystemMessage

from ..core.crypto import encrypt_token, decrypt_token
from ..core.llm import get_llm_service
from ..core.logging import get_logger
from ..clients.google_business_client import get_google_business_client
from ..repositories.business_profile_repository import BusinessProfileRepository
from ..repositories.review_repository import ReviewConnectionRepository, ReviewRepository
from ..tools.review_responder.agent_tools import analyze_review_sentiment

logger = get_logger("reputation_service")

TONES = ["professional", "friendly", "apologetic"]

DRAFT_PROMPT = """You are helping a small business owner reply to a customer review.

Business: {business_name}
Review rating: {rating} out of 5
Review: "{review_text}"

Write THREE reply drafts, one per tone: professional, friendly, apologetic.
Rules: 2-4 sentences each; address the customer's specific points; do not invent
promises (refunds, discounts, free items) unless the review itself implies one; sign off naturally.

Return ONLY valid JSON: {{"professional": "...", "friendly": "...", "apologetic": "..."}}"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ReputationService:
    def __init__(self, db: Client):
        self.db = db
        self.connections = ReviewConnectionRepository(db)
        self.reviews = ReviewRepository(db)
        self.profiles = BusinessProfileRepository(db)
        self.google = get_google_business_client()

    # ---- connection / OAuth ----

    def build_auth_url(self, business_profile_id: str) -> str:
        """Build a Google OAuth URL with the profile id carried in encrypted state."""
        state = encrypt_token(json.dumps({"bid": business_profile_id, "ts": time.time()}))
        return self.google.get_authorization_url(state)

    async def complete_connection(self, code: str, state: str) -> dict[str, Any]:
        """Exchange the OAuth code, discover the location, and store encrypted tokens."""
        payload = json.loads(decrypt_token(state))
        business_profile_id = payload["bid"]

        tokens = await self.google.exchange_code(code)
        access = tokens["access_token"]

        accounts = await self.google.list_accounts(access)
        if not accounts:
            raise ValueError("No Google Business accounts found for this user")
        account = accounts[0]["name"]

        locations = await self.google.list_locations(access, account)
        if not locations:
            raise ValueError("No locations found for this Google Business account")
        location = locations[0]

        conn = await self.connections.upsert(
            business_profile_id=business_profile_id,
            platform="google",
            external_account_id=account,
            external_location_id=location["name"],
            location_label=location.get("title"),
            access_token=encrypt_token(access),
            refresh_token=encrypt_token(tokens.get("refresh_token")),
            token_expires_at=datetime.fromtimestamp(tokens["expires_at"], timezone.utc).isoformat(),
            status="connected",
        )
        return {"connection": self._safe(conn), "business_profile_id": business_profile_id}

    async def list_connections(self, business_profile_id: str) -> list[dict[str, Any]]:
        conns = await self.connections.get_for_profile(business_profile_id)
        return [self._safe(c) for c in conns]

    @staticmethod
    def _safe(conn: dict[str, Any]) -> dict[str, Any]:
        """Strip secret token fields before returning a connection to the client."""
        return {k: v for k, v in conn.items() if k not in ("access_token", "refresh_token")}

    async def _access_token(self, conn: dict[str, Any]) -> str:
        """Return a valid access token, refreshing and persisting if near expiry."""
        expires_at = conn.get("token_expires_at")
        near_expiry = not expires_at or _parse_iso(expires_at) <= datetime.now(
            timezone.utc
        ) + timedelta(minutes=5)
        if not near_expiry:
            return decrypt_token(conn["access_token"])

        refresh = decrypt_token(conn.get("refresh_token"))
        if not refresh:
            raise ValueError("Connection has no refresh token; reconnect required")
        tokens = await self.google.refresh_access_token(refresh)
        await self.connections.update(
            conn["id"],
            access_token=encrypt_token(tokens["access_token"]),
            token_expires_at=datetime.fromtimestamp(tokens["expires_at"], timezone.utc).isoformat(),
        )
        return tokens["access_token"]

    # ---- sync ----

    async def sync_reviews(self, business_profile_id: str) -> dict[str, Any]:
        conn = await self.connections.get_connected(business_profile_id, "google")
        if not conn:
            return {"synced": 0, "status": "not_connected"}
        try:
            token = await self._access_token(conn)
            account, location = conn["external_account_id"], conn["external_location_id"]
            raw_reviews = await self.google.list_reviews(token, account, location)
            count = 0
            for raw in raw_reviews:
                normalized = self.google.normalize_review(raw, account, location)
                if not normalized["external_review_id"]:
                    continue
                self._apply_sentiment(normalized)
                await self.reviews.upsert(
                    business_profile_id=business_profile_id,
                    connection_id=conn["id"],
                    source="google",
                    synced_at=_now_iso(),
                    **normalized,
                )
                count += 1
            await self.connections.update(
                conn["id"], last_sync_at=_now_iso(), last_sync_status="ok"
            )
            logger.info(
                "Synced Google reviews", business_profile_id=business_profile_id, count=count
            )
            return {"synced": count, "status": "ok"}
        except Exception as e:
            logger.error(
                "Review sync failed", error=str(e), business_profile_id=business_profile_id
            )
            await self.connections.update(
                conn["id"], last_sync_status="error", last_error=str(e)[:500]
            )
            return {"synced": 0, "status": "error", "error": str(e)}

    def _apply_sentiment(self, review: dict[str, Any]) -> None:
        """Classify sentiment + themes in place using the shared keyword classifier."""
        text = (review.get("review_text") or "").strip()
        if not text:
            review.update(sentiment="neutral", sentiment_confidence=0.3, themes=[])
            return
        result = json.loads(
            analyze_review_sentiment.invoke(
                {"review_text": text, "review_rating": review.get("rating")}
            )
        )
        themes = [t for t in result.get("key_issues", []) if t != "No specific issues identified"]
        pos, neg = result.get("positive_mentions", 0), result.get("negative_mentions", 0)
        review.update(
            sentiment=result.get("sentiment", "neutral"),
            sentiment_confidence=round(min(0.95, 0.5 + 0.1 * abs(pos - neg)), 2),
            themes=themes,
        )

    # ---- drafting ----

    async def generate_drafts(self, review_id: str) -> dict[str, Any]:
        review = await self.reviews.get_by_id(review_id)
        if not review:
            raise ValueError("Review not found")
        profile = await self.profiles.get_by_id(review["business_profile_id"])
        business_name = (profile or {}).get("business_name") or "our team"

        llm = get_llm_service().get_llm()
        prompt = DRAFT_PROMPT.format(
            business_name=business_name,
            rating=review.get("rating") or "n/a",
            review_text=(review.get("review_text") or "")[:1000],
        )
        message = await llm.ainvoke(
            [
                SystemMessage(content="You write concise, on-brand review replies."),
                HumanMessage(content=prompt),
            ]
        )
        drafts = self._parse_drafts(message.content)
        if review.get("response_status") == "needs_response":
            await self.reviews.update(review_id, response_status="drafted")
        return {"drafts": drafts}

    @staticmethod
    def _parse_drafts(content: str) -> list[dict[str, str]]:
        try:
            start, end = content.find("{"), content.rfind("}")
            data = json.loads(content[start : end + 1])
            drafts = [{"tone": t, "text": data[t]} for t in TONES if t in data]
            if drafts:
                return drafts
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        return [{"tone": "professional", "text": content.strip()}]

    # ---- publishing ----

    async def publish_reply(self, review_id: str, text: str) -> dict[str, Any]:
        review = await self.reviews.get_by_id(review_id)
        if not review:
            raise ValueError("Review not found")

        if review["source"] == "google":
            conn = None
            if review.get("connection_id"):
                conn = await self.connections.get_by_id(review["connection_id"])
            conn = conn or await self.connections.get_connected(review["business_profile_id"])
            if not conn:
                raise ValueError("Google connection not found; reconnect required")
            token = await self._access_token(conn)
            review_name = (
                f"{conn['external_account_id']}/{conn['external_location_id']}"
                f"/reviews/{review['external_review_id']}"
            )
            await self.google.update_reply(token, review_name, text)

        updated = await self.reviews.update(
            review_id,
            response_text=text,
            response_status="responded",
            response_published_at=_now_iso(),
        )
        return {"review": updated}

    # ---- manual add (universal fallback / pre-approval testing) ----

    async def add_manual_review(
        self,
        business_profile_id: str,
        author_name: str | None,
        rating: int | None,
        review_text: str,
    ) -> dict[str, Any]:
        normalized = {
            "external_review_id": f"manual-{uuid.uuid4()}",
            "author_name": author_name,
            "rating": rating,
            "review_text": review_text,
            "review_created_at": _now_iso(),
        }
        self._apply_sentiment(normalized)
        review = await self.reviews.upsert(
            business_profile_id=business_profile_id, source="manual", **normalized
        )
        return {"review": review}

    # ---- analytics ----

    async def get_analytics(self, business_profile_id: str) -> dict[str, Any]:
        rows = await self.reviews.get_all_for_profile(business_profile_id)
        total = len(rows)
        rated = [r["rating"] for r in rows if r.get("rating")]
        sentiment_counts = Counter(r.get("sentiment") or "neutral" for r in rows)
        responded = sum(1 for r in rows if r.get("response_status") == "responded")
        themes = Counter(t for r in rows for t in (r.get("themes") or []))

        now = datetime.now(timezone.utc)
        recent, prior = [], []
        for r in rows:
            if not r.get("rating") or not r.get("review_created_at"):
                continue
            age = (now - _parse_iso(r["review_created_at"])).days
            if age <= 30:
                recent.append(r["rating"])
            elif age <= 60:
                prior.append(r["rating"])

        avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else None  # noqa: E731
        return {
            "total_reviews": total,
            "average_rating": avg(rated),
            "needs_response": sum(1 for r in rows if r.get("response_status") != "responded"),
            "response_rate": round(responded / total, 2) if total else 0,
            "sentiment": {
                key: sentiment_counts.get(key, 0)
                for key in ("positive", "neutral", "mixed", "negative")
            },
            "top_themes": [{"theme": t, "count": c} for t, c in themes.most_common(5)],
            "rating_trend": {"recent_30d": avg(recent), "prior_30d": avg(prior)},
        }
