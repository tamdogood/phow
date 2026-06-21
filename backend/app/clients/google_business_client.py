"""Google Business Profile API client: OAuth + reviews read/reply.

Reviews are served by the legacy My Business v4 API; accounts/locations come from the
newer Account Management and Business Information v1 APIs. All require the
`business.manage` OAuth scope and Google-approved API access.
"""

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("google_business")

SCOPE = "https://www.googleapis.com/auth/business.manage"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ACCOUNTS_URL = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
LOCATIONS_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"
REVIEWS_URL = "https://mybusiness.googleapis.com/v4"

STAR_RATING = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}


class GoogleBusinessClient:
    """Client for the Google Business Profile API."""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.google_oauth_client_id
        self.client_secret = settings.google_oauth_client_secret
        self.redirect_uri = settings.google_oauth_redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Build the OAuth consent URL (offline access for a refresh token)."""
        if not self.client_id:
            raise RuntimeError("GOOGLE_OAUTH_CLIENT_ID is not configured")
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange an authorization code for access + refresh tokens."""
        return await self._token_request(
            {
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            }
        )

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Get a fresh access token from a stored refresh token."""
        return await self._token_request(
            {"refresh_token": refresh_token, "grant_type": "refresh_token"}
        )

    async def _token_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = {**payload, "client_id": self.client_id, "client_secret": self.client_secret}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(TOKEN_URL, data=payload)
        res.raise_for_status()
        data = res.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": time.time() + data.get("expires_in", 3600),
        }

    async def list_accounts(self, access_token: str) -> list[dict[str, Any]]:
        data = await self._get(ACCOUNTS_URL, access_token)
        return data.get("accounts", [])

    async def list_locations(self, access_token: str, account: str) -> list[dict[str, Any]]:
        url = f"{LOCATIONS_URL}/{account}/locations"
        data = await self._get(url, access_token, params={"readMask": "name,title"})
        return data.get("locations", [])

    async def list_reviews(
        self, access_token: str, account: str, location: str
    ) -> list[dict[str, Any]]:
        """List reviews for a location (account="accounts/123", location="locations/456")."""
        url = f"{REVIEWS_URL}/{account}/{location}/reviews"
        reviews: list[dict[str, Any]] = []
        page_token: str | None = None
        for _ in range(20):  # safety cap
            params = {"pageSize": 50}
            if page_token:
                params["pageToken"] = page_token
            data = await self._get(url, access_token, params=params)
            reviews.extend(data.get("reviews", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return reviews

    async def update_reply(
        self, access_token: str, review_name: str, comment: str
    ) -> dict[str, Any]:
        """Publish/overwrite the owner reply on a review."""
        url = f"{REVIEWS_URL}/{review_name}/reply"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.put(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                json={"comment": comment},
            )
        res.raise_for_status()
        return res.json()

    async def _get(self, url: str, access_token: str, params: dict | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                url, headers={"Authorization": f"Bearer {access_token}"}, params=params
            )
        res.raise_for_status()
        return res.json()

    @staticmethod
    def normalize_review(raw: dict[str, Any], account: str, location: str) -> dict[str, Any]:
        """Map a Google v4 review payload to our normalized review fields."""
        reviewer = raw.get("reviewer", {})
        reply = raw.get("reviewReply")
        review_id = raw.get("reviewId", "")
        normalized = {
            "external_review_id": review_id,
            "author_name": reviewer.get("displayName"),
            "author_photo_url": reviewer.get("profilePhotoUrl"),
            "rating": STAR_RATING.get(raw.get("starRating", "")),
            "review_text": raw.get("comment"),
            "review_created_at": raw.get("createTime"),
            "review_url": None,
            "raw_payload": raw,
        }
        if reply:
            normalized["response_status"] = "responded"
            normalized["response_text"] = reply.get("comment")
            normalized["response_published_at"] = reply.get("updateTime")
        return normalized


def get_google_business_client() -> GoogleBusinessClient:
    return GoogleBusinessClient()
