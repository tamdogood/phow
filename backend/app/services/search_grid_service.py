import math
from typing import Any
from supabase import Client
from ..repositories.search_grid_repository import SearchGridRepository
from ..repositories.business_profile_repository import BusinessProfileRepository
from ..tools.location_scout.google_maps import GoogleMapsClient
from ..core.logging import get_logger

logger = get_logger("search_grid_service")


class SearchGridService:
    def __init__(self, db: Client):
        self.repo = SearchGridRepository(db)
        self.profile_repo = BusinessProfileRepository(db)
        self.maps = GoogleMapsClient()

    @staticmethod
    def calculate_grid_points(
        center_lat: float, center_lng: float, radius_km: float, grid_size: int
    ) -> list[dict[str, Any]]:
        step_km = (radius_km * 2) / (grid_size - 1)
        points = []
        half = grid_size // 2
        lat_step = step_km / 111.32
        lng_step = step_km / (111.32 * math.cos(math.radians(center_lat)))

        for row in range(grid_size):
            for col in range(grid_size):
                points.append(
                    {
                        "row": row,
                        "col": col,
                        "lat": round(center_lat + (row - half) * lat_step, 7),
                        "lng": round(center_lng + (col - half) * lng_step, 7),
                    }
                )
        return points

    async def create_report(
        self,
        business_profile_id: str,
        name: str,
        keywords: list[str],
        radius_km: float = 5,
        grid_size: int = 7,
        frequency: str = "weekly",
        schedule_day: int = 5,
        schedule_hour: int = 9,
        timezone: str = "America/New_York",
        notify_email: str | None = None,
    ) -> dict[str, Any]:
        profile = await self.profile_repo.get_by_id(business_profile_id)
        if not profile:
            raise ValueError("Business profile not found")

        center_lat = profile.get("location_lat")
        center_lng = profile.get("location_lng")

        if not center_lat or not center_lng:
            address = profile.get("location_address")
            if not address:
                raise ValueError("Business profile has no address or coordinates")
            geo = await self.maps.geocode(address)
            if not geo:
                raise ValueError(f"Could not geocode address: {address}")
            center_lat = geo["lat"]
            center_lng = geo["lng"]
            await self.profile_repo.update(
                business_profile_id,
                location_lat=center_lat,
                location_lng=center_lng,
                location_place_id=geo.get("place_id"),
            )

        # Find the actual Google Maps business listing place_id (not geocode place_id)
        place_id = profile.get("location_place_id")
        business_name = profile.get("business_name")
        if business_name and center_lat and center_lng:
            found = await self.maps.find_place(business_name, center_lat, center_lng)
            if found:
                place_id = found["place_id"]
                logger.info("Found business listing", place_id=place_id, name=found.get("name"))

        report = await self.repo.create_report(
            {
                "business_profile_id": business_profile_id,
                "name": name,
                "center_lat": center_lat,
                "center_lng": center_lng,
                "center_address": profile.get("location_address"),
                "place_id": place_id,
                "radius_km": radius_km,
                "grid_size": grid_size,
                "keywords": keywords,
                "frequency": frequency,
                "schedule_day": schedule_day,
                "schedule_hour": schedule_hour,
                "timezone": timezone,
                "notify_email": notify_email,
                "status": "pending",
            }
        )

        try:
            from ..workers.search_grid_tasks import run_search_grid

            run_search_grid.delay(report["id"])
        except Exception as e:
            logger.warning("Failed to dispatch Celery task", report_id=report["id"], error=str(e))

        logger.info("Search grid report created", report_id=report["id"])
        return report

    async def get_report_with_results(self, report_id: str) -> dict[str, Any] | None:
        report = await self.repo.get_report(report_id)
        if not report:
            return None
        latest_run = await self.repo.get_latest_run(report_id)
        results = []
        if latest_run:
            results = await self.repo.get_results(latest_run["id"])
        return {**report, "latest_run": latest_run, "results": results}

    async def list_reports_summary(self, business_profile_id: str) -> list[dict[str, Any]]:
        reports = await self.repo.list_reports(business_profile_id)
        summaries = []
        for r in reports:
            latest_run = await self.repo.get_latest_run(r["id"])
            summaries.append(
                {
                    **r,
                    "avg_rank": latest_run["avg_rank"] if latest_run else None,
                    "top3_pct": latest_run["top3_pct"] if latest_run else None,
                    "run_status": latest_run["status"] if latest_run else None,
                }
            )
        return summaries

    async def trigger_run(self, report_id: str) -> dict[str, Any]:
        report = await self.repo.get_report(report_id)
        if not report:
            raise ValueError("Report not found")
        await self.repo.update_report(report_id, {"status": "running"})
        try:
            from ..workers.search_grid_tasks import run_search_grid

            run_search_grid.delay(report_id)
        except Exception as e:
            logger.warning("Failed to dispatch Celery task", report_id=report_id, error=str(e))
        return {"report_id": report_id, "status": "running"}

    async def update_report(self, report_id: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self.repo.update_report(report_id, data)

    async def delete_report(self, report_id: str) -> bool:
        return await self.repo.delete_report(report_id)

    async def get_run_results(
        self, run_id: str, keyword: str | None = None
    ) -> list[dict[str, Any]]:
        return await self.repo.get_results(run_id, keyword)

    async def get_runs(self, report_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.repo.get_runs(report_id, limit)

    async def get_result_detail(self, result_id: str) -> dict[str, Any] | None:
        return await self.repo.get_result_detail(result_id)

    async def get_aggregated_competitors(
        self, run_id: str, keyword: str | None = None
    ) -> list[dict[str, Any]]:
        return await self.repo.get_aggregated_competitors(run_id, keyword)
