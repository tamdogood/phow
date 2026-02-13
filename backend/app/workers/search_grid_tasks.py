"""Celery tasks for search grid analysis."""

import uuid
from typing import Any
from .celery_app import celery_app
from .tasks import run_async
from ..core.logging import get_logger
from ..api.deps import get_supabase

logger = get_logger("search_grid_tasks")


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

            # Resolve actual business listing place_id
            profile = db.table("business_profiles").select("business_name").eq("id", report["business_profile_id"]).execute()
            biz_name = profile.data[0]["business_name"] if profile.data else None
            if biz_name:
                found = await maps.find_place(biz_name, center_lat, center_lng)
                if found:
                    place_id = found["place_id"]
                    await repo.update_report(report_id, {"place_id": place_id})

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

                        if place_id:
                            for i, place in enumerate(nearby[:20]):
                                if place.get("place_id") == place_id:
                                    rank = i + 1
                                    break

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

            await repo.update_run(
                run_id,
                {
                    "status": "completed",
                    "points_completed": total,
                    "avg_rank": avg_rank,
                    "top3_pct": top3_pct,
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
