"""Connection lifecycle service for review providers."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from supabase import Client

from ..clients.reviews import GoogleReviewsClient, YelpReviewsClient, MetaReviewsClient
from ..core.config import get_settings
from ..core.crypto import get_token_cipher
from ..repositories.reviews_repository import ReviewSourceRepository, ReviewActivityLogRepository
from .review_errors import ValidationFailedError, ProviderUnavailableError


SUPPORTED_SOURCES = {"google", "yelp", "meta"}


class ConnectionService:
    """Manages connector auth and source lifecycle."""

    def __init__(self, db: Client):
        self.source_repo = ReviewSourceRepository(db)
        self.activity_repo = ReviewActivityLogRepository(db)
        self.settings = get_settings()
        self.cipher = get_token_cipher()
        self.google_client = GoogleReviewsClient()
        self.yelp_client = YelpReviewsClient()
        self.meta_client = MetaReviewsClient()

    def _validate_source(self, source: str):
        if source not in SUPPORTED_SOURCES:
            raise ValidationFailedError(f"Unsupported source '{source}'")

    async def list_connections(self, business_profile_id: str) -> list[dict]:
        rows = await self.source_repo.list_by_profile(business_profile_id)
        by_source = {row["source"]: row for row in rows}

        normalized = []
        for source in sorted(SUPPORTED_SOURCES):
            row = by_source.get(source)
            normalized.append(
                {
                    "source": source,
                    "status": row.get("status") if row else "disconnected",
                    "connected_at": row.get("connected_at") if row else None,
                    "last_synced_at": row.get("last_synced_at") if row else None,
                    "last_error": row.get("last_error") if row else None,
                    "has_refresh_token": bool(row and row.get("refresh_token_encrypted")),
                    "metadata": row.get("metadata") if row else {},
                }
            )
        return normalized

    async def start_connection(
        self,
        *,
        business_profile_id: str,
        source: str,
        actor_session_id: str | None,
        actor_user_id: str | None,
    ) -> dict:
        self._validate_source(source)
        if not self.settings.reputation_live_connectors_enabled:
            raise ProviderUnavailableError("Live connectors are disabled")

        if source == "google":
            if not self.settings.reputation_oauth_enabled:
                raise ProviderUnavailableError("OAuth flow is disabled")

            state = secrets.token_urlsafe(24)
            auth_url = self.google_client.get_authorization_url(state)
            await self.source_repo.upsert(
                business_profile_id,
                source,
                status="pending",
                oauth_state=state,
                metadata={"oauth_url_generated_at": datetime.now(timezone.utc).isoformat()},
            )
            await self.activity_repo.log(
                business_profile_id=business_profile_id,
                source=source,
                action="connection_start",
                actor_session_id=actor_session_id,
                actor_user_id=actor_user_id,
                details={"mode": "oauth"},
            )
            return {"source": source, "mode": "oauth", "authorization_url": auth_url}

        if source == "yelp":
            payload = self.yelp_client.get_connection_payload()
            row = await self.source_repo.upsert(
                business_profile_id,
                source,
                status="connected",
                connected_at=datetime.now(timezone.utc).isoformat(),
                metadata=payload,
            )
            await self.activity_repo.log(
                business_profile_id=business_profile_id,
                source=source,
                action="connection_start",
                actor_session_id=actor_session_id,
                actor_user_id=actor_user_id,
                details={"mode": "api_key"},
            )
            return {
                "source": source,
                "mode": "api_key",
                "status": row.get("status", "connected"),
                "deeplink": payload.get("deeplink"),
            }

        raise ProviderUnavailableError("Meta connection is not available in MVP")

    async def callback_connection(
        self,
        *,
        business_profile_id: str,
        source: str,
        code: str | None,
        state: str | None,
        actor_session_id: str | None,
        actor_user_id: str | None,
    ) -> dict:
        self._validate_source(source)

        if source != "google":
            raise ValidationFailedError("Callback is only supported for google source")
        if not code:
            raise ValidationFailedError("code is required for callback")

        existing = await self.source_repo.get_by_profile_source(business_profile_id, source)
        expected_state = existing.get("oauth_state") if existing else None
        if expected_state and state and expected_state != state:
            raise ValidationFailedError("Invalid oauth state")

        token_data = await self.google_client.exchange_code(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_at_epoch = token_data.get("expires_at")
        expires_at_iso = (
            datetime.fromtimestamp(expires_at_epoch, tz=timezone.utc).isoformat()
            if expires_at_epoch
            else None
        )

        row = await self.source_repo.upsert(
            business_profile_id,
            source,
            status="connected",
            oauth_state=None,
            access_token_encrypted=self.cipher.encrypt(access_token),
            refresh_token_encrypted=self.cipher.encrypt(refresh_token),
            token_expires_at=expires_at_iso,
            connected_at=datetime.now(timezone.utc).isoformat(),
            metadata={"provider": "google", "token_payload": token_data.get("raw") or {}},
            last_error=None,
        )

        await self.activity_repo.log(
            business_profile_id=business_profile_id,
            source=source,
            action="connection_callback",
            actor_session_id=actor_session_id,
            actor_user_id=actor_user_id,
            details={"status": "connected"},
        )

        return {
            "source": source,
            "status": row.get("status", "connected"),
            "connected_at": row.get("connected_at"),
            "token_expires_at": row.get("token_expires_at"),
        }

    async def disconnect(
        self,
        *,
        business_profile_id: str,
        source: str,
        actor_session_id: str | None,
        actor_user_id: str | None,
    ) -> dict:
        self._validate_source(source)

        row = await self.source_repo.disconnect(business_profile_id, source)
        if not row:
            raise ValidationFailedError(f"No connection found for source '{source}'")

        await self.activity_repo.log(
            business_profile_id=business_profile_id,
            source=source,
            action="connection_disconnect",
            actor_session_id=actor_session_id,
            actor_user_id=actor_user_id,
            details={"status": "disconnected"},
        )

        return {"source": source, "status": "disconnected"}
