"""Google reviews connector client."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx

from ...core.config import get_settings
from ...core.logging import get_logger
from ...services.review_errors import ProviderUnavailableError, AuthExpiredError

logger = get_logger("google_reviews_client")

GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_BUSINESS_REVIEWS_URL = "https://mybusiness.googleapis.com/v4/accounts/{account_id}/locations/{location_id}/reviews"


class GoogleReviewsClient:
    """Minimal Google Business Profile integration for OAuth and reviews fetch."""

    def __init__(self):
        self.settings = get_settings()

    def get_authorization_url(self, state: str) -> str:
        if not self.settings.google_oauth_client_id or not self.settings.google_oauth_redirect_uri:
            raise ProviderUnavailableError("Google OAuth credentials are not configured")

        params = {
            "client_id": self.settings.google_oauth_client_id,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/business.manage",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_OAUTH_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict:
        if not self.settings.google_oauth_client_id or not self.settings.google_oauth_client_secret:
            raise ProviderUnavailableError("Google OAuth credentials are not configured")

        payload = {
            "code": code,
            "client_id": self.settings.google_oauth_client_id,
            "client_secret": self.settings.google_oauth_client_secret,
            "redirect_uri": self.settings.google_oauth_redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=payload)

        if response.status_code >= 400:
            raise ProviderUnavailableError(f"Google token exchange failed ({response.status_code})")

        data = response.json()
        expires_at = None
        expires_in = data.get("expires_in")
        if expires_in:
            expires_at = datetime.now(timezone.utc).timestamp() + int(expires_in)

        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": expires_at,
            "raw": data,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = {
            "refresh_token": refresh_token,
            "client_id": self.settings.google_oauth_client_id,
            "client_secret": self.settings.google_oauth_client_secret,
            "grant_type": "refresh_token",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=payload)

        if response.status_code >= 400:
            raise AuthExpiredError("Google token refresh failed")

        data = response.json()
        expires_at = None
        if data.get("expires_in"):
            expires_at = datetime.now(timezone.utc).timestamp() + int(data["expires_in"])

        return {
            "access_token": data.get("access_token"),
            "expires_at": expires_at,
            "raw": data,
        }

    async def list_reviews(self, access_token: str) -> list[dict]:
        account_id = self.settings.google_business_account_id
        location_id = self.settings.google_business_location_id

        if not account_id or not location_id:
            raise ProviderUnavailableError("Google business account/location is not configured")

        url = GOOGLE_BUSINESS_REVIEWS_URL.format(account_id=account_id, location_id=location_id)
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 401:
            raise AuthExpiredError()
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"Google reviews fetch failed ({response.status_code})")

        payload = response.json() or {}
        items = payload.get("reviews", [])
        normalized = []
        for item in items:
            name = item.get("name", "")
            external_id = name.split("/")[-1] if name else item.get("reviewId")
            normalized.append(
                {
                    "source": "google",
                    "external_review_id": external_id,
                    "external_url": item.get("reviewReply", {}).get("updateTime"),
                    "reviewer_name": (item.get("reviewer") or {}).get("displayName"),
                    "rating": int(item.get("starRating", 0) or 0),
                    "title": None,
                    "content": item.get("comment") or "",
                    "review_created_at": item.get("createTime"),
                    "raw_payload": item,
                }
            )
        logger.info("Fetched Google reviews", count=len(normalized))
        return normalized
