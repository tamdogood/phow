"""Analytics and competitor comparison service for Reputation Hub."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from supabase import Client

from ..repositories.business_profile_repository import TrackedCompetitorRepository
from ..repositories.reviews_repository import ReviewRepository, ReviewSentimentRepository


class ReviewAnalyticsService:
    """Computes summary/trend/theme/platform metrics from persisted data."""

    def __init__(self, db: Client):
        self.review_repo = ReviewRepository(db)
        self.sentiment_repo = ReviewSentimentRepository(db)
        self.competitor_repo = TrackedCompetitorRepository(db)

    async def _load_reviews(self, business_profile_id: str, days: int) -> tuple[list[dict], dict[str, dict]]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        reviews = await self.review_repo.list_by_profile(
            business_profile_id,
            start_at=start.isoformat(),
            end_at=end.isoformat(),
        )
        sentiments = await self.sentiment_repo.list_by_review_ids([r["id"] for r in reviews])
        by_review_id = {row["review_id"]: row for row in sentiments}
        return reviews, by_review_id

    async def summary(self, business_profile_id: str, days: int = 30) -> dict:
        reviews, sentiments = await self._load_reviews(business_profile_id, days)
        total = len(reviews)
        replied = len([r for r in reviews if r.get("reply_status") == "replied"])
        avg_rating = round(sum((r.get("rating") or 0) for r in reviews) / total, 2) if total else 0.0

        sentiment_counter = Counter()
        for review in reviews:
            label = (sentiments.get(review["id"]) or {}).get("sentiment_label", "unknown")
            sentiment_counter[label] += 1

        return {
            "window_days": days,
            "total_reviews": total,
            "replied_reviews": replied,
            "response_rate": round((replied / total) * 100, 2) if total else 0.0,
            "avg_rating": avg_rating,
            "sentiment_distribution": dict(sentiment_counter),
        }

    async def trends(self, business_profile_id: str, days: int = 30) -> list[dict]:
        reviews, sentiments = await self._load_reviews(business_profile_id, days)
        daily = defaultdict(lambda: {"review_count": 0, "rating_sum": 0, "positive": 0, "negative": 0})

        for review in reviews:
            timestamp = review.get("review_created_at") or review.get("created_at")
            day_key = str(timestamp)[:10]
            daily[day_key]["review_count"] += 1
            daily[day_key]["rating_sum"] += int(review.get("rating") or 0)
            label = (sentiments.get(review["id"]) or {}).get("sentiment_label")
            if label == "positive":
                daily[day_key]["positive"] += 1
            if label == "negative":
                daily[day_key]["negative"] += 1

        points = []
        for day, metrics in sorted(daily.items()):
            count = metrics["review_count"]
            points.append(
                {
                    "date": day,
                    "review_count": count,
                    "avg_rating": round(metrics["rating_sum"] / count, 2) if count else 0.0,
                    "positive_count": metrics["positive"],
                    "negative_count": metrics["negative"],
                }
            )

        return points

    async def themes(self, business_profile_id: str, days: int = 30) -> list[dict]:
        reviews, sentiments = await self._load_reviews(business_profile_id, days)
        counts = Counter()

        for review in reviews:
            sentiment = sentiments.get(review["id"])
            if not sentiment:
                continue
            for theme in sentiment.get("themes") or []:
                counts[theme] += 1

        return [{"theme": theme, "count": count} for theme, count in counts.most_common()]

    async def platforms(self, business_profile_id: str, days: int = 30) -> list[dict]:
        reviews, _ = await self._load_reviews(business_profile_id, days)
        metrics = defaultdict(lambda: {"count": 0, "rating_sum": 0, "replied": 0})

        for review in reviews:
            source = review.get("source") or "unknown"
            metrics[source]["count"] += 1
            metrics[source]["rating_sum"] += int(review.get("rating") or 0)
            if review.get("reply_status") == "replied":
                metrics[source]["replied"] += 1

        rows = []
        for source, data in sorted(metrics.items()):
            count = data["count"]
            rows.append(
                {
                    "source": source,
                    "review_count": count,
                    "avg_rating": round(data["rating_sum"] / count, 2) if count else 0.0,
                    "response_rate": round((data["replied"] / count) * 100, 2) if count else 0.0,
                }
            )
        return rows

    async def competitors(self, business_profile_id: str) -> list[dict]:
        competitors = await self.competitor_repo.get_competitors(business_profile_id)
        return [
            {
                "id": comp.get("id"),
                "name": comp.get("name"),
                "rating": comp.get("rating"),
                "review_count": comp.get("review_count"),
                "price_level": comp.get("price_level"),
                "address": comp.get("address"),
            }
            for comp in competitors
        ]
