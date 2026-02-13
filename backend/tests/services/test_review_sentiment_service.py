"""Tests for review sentiment service."""

import pytest

from app.services.review_sentiment_service import ReviewSentimentService


class DummySentimentRepo:
    async def upsert(self, **kwargs):
        return kwargs


@pytest.mark.asyncio
async def test_classify_and_persist_positive_review():
    service = ReviewSentimentService(DummySentimentRepo())

    saved = await service.classify_and_persist(
        {
            "id": "review-1",
            "rating": 5,
            "content": "Great service and amazing quality",
        }
    )

    assert saved["sentiment_label"] == "positive"
    assert saved["review_id"] == "review-1"
    assert "service" in saved["themes"]


@pytest.mark.asyncio
async def test_classify_and_persist_negative_review():
    service = ReviewSentimentService(DummySentimentRepo())

    saved = await service.classify_and_persist(
        {
            "id": "review-2",
            "rating": 1,
            "content": "Terrible and rude staff",
        }
    )

    assert saved["sentiment_label"] == "negative"
    assert saved["sentiment_score"] <= 0.33
