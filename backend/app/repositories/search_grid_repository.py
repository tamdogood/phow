import uuid
from typing import Any
from .base import BaseRepository


class SearchGridRepository(BaseRepository):

    async def create_report(self, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = str(uuid.uuid4())
        result = self.db.table("search_grid_reports").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        result = self.db.table("search_grid_reports").select("*").eq("id", report_id).execute()
        return result.data[0] if result.data else None

    async def list_reports(self, business_profile_id: str) -> list[dict[str, Any]]:
        result = (
            self.db.table("search_grid_reports")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    async def update_report(self, report_id: str, data: dict[str, Any]) -> dict[str, Any]:
        result = self.db.table("search_grid_reports").update(data).eq("id", report_id).execute()
        return result.data[0] if result.data else {}

    async def delete_report(self, report_id: str) -> bool:
        result = self.db.table("search_grid_reports").delete().eq("id", report_id).execute()
        return bool(result.data)

    async def create_run(self, report_id: str, points_total: int) -> dict[str, Any]:
        data = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "points_total": points_total,
            "status": "running",
        }
        result = self.db.table("search_grid_runs").insert(data).execute()
        return result.data[0] if result.data else {}

    async def update_run(self, run_id: str, data: dict[str, Any]) -> dict[str, Any]:
        result = self.db.table("search_grid_runs").update(data).eq("id", run_id).execute()
        return result.data[0] if result.data else {}

    async def get_latest_run(self, report_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("search_grid_runs")
            .select("*")
            .eq("report_id", report_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_runs(self, report_id: str, limit: int = 10) -> list[dict[str, Any]]:
        result = (
            self.db.table("search_grid_runs")
            .select("*")
            .eq("report_id", report_id)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def save_results(self, results: list[dict[str, Any]]) -> None:
        if not results:
            return
        self.db.table("search_grid_results").insert(results).execute()

    async def get_results(self, run_id: str, keyword: str | None = None) -> list[dict[str, Any]]:
        cols = "id,run_id,report_id,keyword,grid_row,grid_col,point_lat,point_lng,rank,total_results,top_result_name,score"
        query = self.db.table("search_grid_results").select(cols).eq("run_id", run_id)
        if keyword:
            query = query.eq("keyword", keyword)
        result = query.execute()
        return result.data or []

    async def get_result_detail(self, result_id: str) -> dict[str, Any] | None:
        result = (
            self.db.table("search_grid_results")
            .select(
                "id,keyword,grid_row,grid_col,point_lat,point_lng,rank,total_results,top_result_name,nearby_places,score"
            )
            .eq("id", result_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_aggregated_competitors(
        self, run_id: str, keyword: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        query = self.db.table("search_grid_results").select("nearby_places").eq("run_id", run_id)
        if keyword:
            query = query.eq("keyword", keyword)
        result = query.execute()
        rows = result.data or []

        # Aggregate: place_id -> stats
        agg: dict[str, dict[str, Any]] = {}
        total_points = len(rows)
        for row in rows:
            places = row.get("nearby_places") or []
            for idx, place in enumerate(places):
                pid = place.get("place_id")
                if not pid:
                    continue
                rank = idx + 1
                if pid not in agg:
                    agg[pid] = {
                        "place_id": pid,
                        "name": place.get("name", ""),
                        "ranks": [],
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                    }
                agg[pid]["ranks"].append(rank)
                if agg[pid]["rating"] is None and place.get("rating") is not None:
                    agg[pid]["rating"] = place["rating"]
                if (
                    agg[pid]["user_ratings_total"] is None
                    and place.get("user_ratings_total") is not None
                ):
                    agg[pid]["user_ratings_total"] = place["user_ratings_total"]

        competitors = []
        for entry in agg.values():
            ranks = entry["ranks"]
            competitors.append(
                {
                    "place_id": entry["place_id"],
                    "name": entry["name"],
                    "avg_rank": round(sum(ranks) / len(ranks), 1),
                    "appearances": len(ranks),
                    "total_points": total_points,
                    "rating": entry["rating"],
                    "user_ratings_total": entry["user_ratings_total"],
                }
            )
        competitors.sort(key=lambda c: (-c["appearances"], c["avg_rank"]))
        return competitors[:limit]
