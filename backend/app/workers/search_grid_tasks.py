"""Celery tasks for search grid analysis."""

import uuid
from typing import Any
from .celery_app import celery_app
from .tasks import run_async
from ..core.logging import get_logger
from ..api.deps import get_supabase

logger = get_logger("search_grid_tasks")


def calculate_score(
    rank: int | None,
    total_results: int,
    nearby_places: list[dict] | None,
    user_rating: float | None = None,
    user_reviews: int | None = None,
) -> int:
    """Calculate composite score (0-100) for a grid point.

    Components:
    - Visibility (0-50): Linear interpolation from rank 1=50 to rank 20=3, not found=0
    - Opportunity (0-30): Lower competition = higher opportunity
    - Competitive advantage (0-20): User's rating/reviews vs competitors
    """
    # Visibility (0-50)
    if rank is not None and 1 <= rank <= 20:
        visibility = round(50 - (rank - 1) * (47 / 19))
    else:
        visibility = 0

    # Opportunity (0-30)
    if total_results == 0:
        opportunity = 30
    elif total_results <= 5:
        opportunity = 25
    elif total_results <= 10:
        opportunity = 15
    else:
        opportunity = 5

    # Competitive advantage (0-20)
    if user_rating is None or not nearby_places:
        advantage = 10  # Neutral default
    else:
        rated = [p for p in nearby_places if p.get("rating")]
        if not rated:
            advantage = 10
        else:
            avg_rating = sum(p["rating"] for p in rated) / len(rated)
            avg_reviews = (
                sum(p.get("user_ratings_total") or 0 for p in rated) / len(rated)
            )
            rating_diff = (user_rating - avg_rating) / 5.0  # Normalized [-1, 1]
            review_diff = 0
            if avg_reviews > 0 and user_reviews:
                review_diff = min(max((user_reviews - avg_reviews) / avg_reviews, -1), 1)
            advantage = round(10 + (rating_diff * 7) + (review_diff * 3))
            advantage = max(0, min(20, advantage))

    return max(0, min(100, visibility + opportunity + advantage))


@celery_app.task(bind=True, max_retries=2, time_limit=1800)
def run_search_grid(self, report_id: str) -> dict[str, Any]:
    """Run a search grid analysis for all keywords x grid points."""
    logger.info("Starting search grid run", report_id=report_id)

    try:

        async def _run():
            from ..repositories.search_grid_repository import SearchGridRepository
            from ..services.search_grid_service import SearchGridService
            from ..tools.location_scout.google_maps import GoogleMapsClient

            db = get_supabase()
            repo = SearchGridRepository(db)
            maps = GoogleMapsClient()

            report = await repo.get_report(report_id)
            if not report:
                raise ValueError(f"Report {report_id} not found")

            place_id = report.get("place_id")
            keywords = report["keywords"]
            grid_size = report["grid_size"]
            radius_km = float(report["radius_km"])
            center_lat = float(report["center_lat"])
            center_lng = float(report["center_lng"])

            # Resolve actual business listing place_id (skip if already set)
            if not place_id:
                profile = (
                    db.table("business_profiles")
                    .select("business_name")
                    .eq("id", report["business_profile_id"])
                    .execute()
                )
                biz_name = profile.data[0]["business_name"] if profile.data else None
                if biz_name:
                    found = await maps.find_place(biz_name, center_lat, center_lng)
                    if found:
                        place_id = found["place_id"]
                        await repo.update_report(report_id, {"place_id": place_id})

            # Fetch user's business details for scoring
            user_rating = None
            user_reviews = None
            if place_id:
                try:
                    user_details = await maps.get_place_details(place_id)
                    if user_details:
                        user_rating = user_details.get("rating")
                        user_reviews = user_details.get("user_ratings_total")
                except Exception:
                    logger.warning("Failed to fetch user place details for scoring")

            points = SearchGridService.calculate_grid_points(
                center_lat, center_lng, radius_km, grid_size
            )
            total = len(points) * len(keywords)

            run = await repo.create_run(report_id, total)
            run_id = run["id"]
            await repo.update_report(report_id, {"status": "running"})

            results = []
            completed = 0

            for keyword in keywords:
                for pt in points:
                    try:
                        nearby = await maps.nearby_search(
                            lat=pt["lat"],
                            lng=pt["lng"],
                            radius=2000,
                            keyword=keyword,
                        )
                        rank = None
                        top_result_name = nearby[0]["name"] if nearby else None
                        seen_ids = set()
                        nearby_places = []
                        for p in nearby[:20]:
                            if p["place_id"] in seen_ids:
                                continue
                            seen_ids.add(p["place_id"])
                            nearby_places.append({
                                "name": p["name"],
                                "place_id": p["place_id"],
                                "rating": p.get("rating"),
                                "user_ratings_total": p.get("user_ratings_total"),
                                "vicinity": p.get("vicinity"),
                                "lat": p.get("lat"),
                                "lng": p.get("lng"),
                                "business_status": p.get("business_status"),
                            })

                        if place_id:
                            for i, place in enumerate(nearby[:20]):
                                if place.get("place_id") == place_id:
                                    rank = i + 1
                                    break

                        score = calculate_score(
                            rank, len(nearby), nearby_places, user_rating, user_reviews
                        )
                        results.append(
                            {
                                "id": str(uuid.uuid4()),
                                "run_id": run_id,
                                "report_id": report_id,
                                "keyword": keyword,
                                "grid_row": pt["row"],
                                "grid_col": pt["col"],
                                "point_lat": pt["lat"],
                                "point_lng": pt["lng"],
                                "rank": rank,
                                "total_results": len(nearby),
                                "top_result_name": top_result_name,
                                "nearby_places": nearby_places,
                                "score": score,
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            "Grid point search failed",
                            keyword=keyword,
                            row=pt["row"],
                            col=pt["col"],
                            error=str(e),
                        )
                        results.append(
                            {
                                "id": str(uuid.uuid4()),
                                "run_id": run_id,
                                "report_id": report_id,
                                "keyword": keyword,
                                "grid_row": pt["row"],
                                "grid_col": pt["col"],
                                "point_lat": pt["lat"],
                                "point_lng": pt["lng"],
                                "rank": None,
                                "total_results": 0,
                                "top_result_name": None,
                                "nearby_places": None,
                                "score": None,
                            }
                        )

                    completed += 1
                    if completed % 10 == 0:
                        await repo.update_run(run_id, {"points_completed": completed})

            # Batch insert all results
            await repo.save_results(results)

            # Calculate stats
            ranked = [r for r in results if r["rank"] is not None]
            avg_rank = round(sum(r["rank"] for r in ranked) / len(ranked), 1) if ranked else None
            top3_count = sum(1 for r in ranked if r["rank"] <= 3)
            top3_pct = round(top3_count / len(results) * 100, 2) if results else 0
            scored = [r for r in results if r.get("score") is not None]
            avg_score = round(sum(r["score"] for r in scored) / len(scored), 2) if scored else None

            await repo.update_run(
                run_id,
                {
                    "status": "completed",
                    "points_completed": total,
                    "avg_rank": avg_rank,
                    "top3_pct": top3_pct,
                    "avg_score": avg_score,
                    "completed_at": "now()",
                },
            )
            await repo.update_report(report_id, {"status": "completed", "last_run_at": "now()"})

            logger.info(
                "Search grid run completed",
                report_id=report_id,
                run_id=run_id,
                avg_rank=avg_rank,
                top3_pct=top3_pct,
            )
            return {
                "run_id": run_id,
                "avg_rank": avg_rank,
                "top3_pct": top3_pct,
                "total_points": total,
            }

        return run_async(_run())

    except Exception as e:
        logger.error("Search grid run failed", report_id=report_id, error=str(e))

        async def _mark_failed():
            db = get_supabase()
            from ..repositories.search_grid_repository import SearchGridRepository

            repo = SearchGridRepository(db)
            await repo.update_report(report_id, {"status": "failed"})

        try:
            run_async(_mark_failed())
        except Exception:
            pass

        raise self.retry(exc=e, countdown=120)
