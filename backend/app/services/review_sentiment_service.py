"""Sentiment classification for reviews."""

from __future__ import annotations

from ..repositories.reviews_repository import ReviewSentimentRepository


class ReviewSentimentService:
    """Deterministic sentiment/theme extraction for MVP."""

    def __init__(self, sentiment_repo: ReviewSentimentRepository):
        self.sentiment_repo = sentiment_repo

    def classify(self, rating: int, content: str | None) -> tuple[str, float, list[str]]:
        text = (content or "").lower()

        positive_words = ["great", "excellent", "love", "amazing", "friendly", "best"]
        negative_words = ["bad", "terrible", "awful", "slow", "rude", "dirty", "cold"]

        score = 0.5
        if rating >= 4:
            score += 0.35
        elif rating <= 2:
            score -= 0.35

        if any(word in text for word in positive_words):
            score += 0.2
        if any(word in text for word in negative_words):
            score -= 0.2

        score = max(0.0, min(1.0, score))

        if score >= 0.67:
            label = "positive"
        elif score <= 0.33:
            label = "negative"
        else:
            label = "neutral"

        themes = []
        keyword_themes = {
            "service": ["service", "staff", "friendly", "rude", "wait"],
            "quality": ["taste", "quality", "fresh", "cold", "burnt"],
            "price": ["price", "expensive", "cheap", "value"],
            "cleanliness": ["clean", "dirty", "hygiene"],
            "speed": ["fast", "slow", "wait"],
        }

        for theme, words in keyword_themes.items():
            if any(word in text for word in words):
                themes.append(theme)

        if not themes:
            themes = ["general"]

        return label, score, themes

    async def classify_and_persist(self, review: dict) -> dict:
        label, score, themes = self.classify(review.get("rating") or 0, review.get("content"))
        return await self.sentiment_repo.upsert(
            review_id=review["id"],
            sentiment_label=label,
            sentiment_score=score,
            themes=themes,
        )
