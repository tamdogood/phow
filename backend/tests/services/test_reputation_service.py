"""Offline tests for Reputation Hub pure logic: normalize, drafts, sentiment, analytics."""

from datetime import datetime, timezone

import pytest

from app.clients.google_business_client import GoogleBusinessClient
from app.services.reputation_service import ReputationService


class TestNormalizeReview:
    def test_maps_google_payload(self):
        raw = {
            "reviewId": "abc",
            "reviewer": {"displayName": "Jane", "profilePhotoUrl": "http://x/p.jpg"},
            "starRating": "FIVE",
            "comment": "Great coffee!",
            "createTime": "2026-01-02T03:04:05Z",
        }
        n = GoogleBusinessClient.normalize_review(raw, "accounts/1", "locations/2")
        assert n["external_review_id"] == "abc"
        assert n["rating"] == 5
        assert n["author_name"] == "Jane"
        assert n["review_text"] == "Great coffee!"
        assert "response_status" not in n  # no reply yet

    def test_captures_existing_owner_reply(self):
        raw = {
            "reviewId": "xyz",
            "starRating": "TWO",
            "comment": "Slow service",
            "reviewReply": {"comment": "Sorry!", "updateTime": "2026-01-03T00:00:00Z"},
        }
        n = GoogleBusinessClient.normalize_review(raw, "accounts/1", "locations/2")
        assert n["rating"] == 2
        assert n["response_status"] == "responded"
        assert n["response_text"] == "Sorry!"


class TestDraftParsing:
    def test_extracts_three_tones_from_messy_json(self):
        content = 'Sure! {"professional": "P", "friendly": "F", "apologetic": "A"} hope that helps'
        drafts = ReputationService._parse_drafts(content)
        assert {d["tone"] for d in drafts} == {"professional", "friendly", "apologetic"}
        assert {d["text"] for d in drafts} == {"P", "F", "A"}

    def test_falls_back_to_single_draft_on_bad_json(self):
        drafts = ReputationService._parse_drafts("no json here")
        assert drafts == [{"tone": "professional", "text": "no json here"}]


class TestSentiment:
    def test_negative_review_classified_with_themes(self):
        service = ReputationService(None)
        review = {"review_text": "Terrible, cold food, rude staff, waited forever", "rating": 1}
        service._apply_sentiment(review)
        assert review["sentiment"] == "negative"
        assert review["themes"]

    def test_positive_review(self):
        service = ReputationService(None)
        review = {"review_text": "Amazing, delicious, friendly staff, the best!", "rating": 5}
        service._apply_sentiment(review)
        assert review["sentiment"] == "positive"

    def test_empty_text_is_neutral(self):
        service = ReputationService(None)
        review = {"review_text": "", "rating": None}
        service._apply_sentiment(review)
        assert review["sentiment"] == "neutral"
        assert review["themes"] == []


class TestAuthUrl:
    def test_requires_client_id(self):
        client = GoogleBusinessClient()
        client.client_id = ""
        with pytest.raises(RuntimeError):
            client.get_authorization_url("state123")

    def test_builds_url_with_scope_and_state(self):
        client = GoogleBusinessClient()
        client.client_id = "cid"
        url = client.get_authorization_url("state123")
        assert "state=state123" in url
        assert "business.manage" in url
        assert "access_type=offline" in url


class TestAnalytics:
    async def test_aggregates_sentiment_rating_themes(self):
        service = ReputationService(None)
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            {
                "rating": 5,
                "sentiment": "positive",
                "response_status": "responded",
                "themes": ["Food Quality"],
                "review_created_at": now,
            },
            {
                "rating": 2,
                "sentiment": "negative",
                "response_status": "needs_response",
                "themes": ["Service Speed", "Food Quality"],
                "review_created_at": now,
            },
            {
                "rating": 4,
                "sentiment": "positive",
                "response_status": "responded",
                "themes": [],
                "review_created_at": now,
            },
        ]

        async def fake_get_all(_):
            return rows

        service.reviews.get_all_for_profile = fake_get_all
        analytics = await service.get_analytics("bid")

        assert analytics["total_reviews"] == 3
        assert analytics["average_rating"] == round((5 + 2 + 4) / 3, 2)
        assert analytics["sentiment"] == {"positive": 2, "neutral": 0, "mixed": 0, "negative": 1}
        assert analytics["needs_response"] == 1
        assert analytics["response_rate"] == round(2 / 3, 2)
        assert analytics["top_themes"][0] == {"theme": "Food Quality", "count": 2}
        assert analytics["rating_trend"]["recent_30d"] == round((5 + 2 + 4) / 3, 2)
