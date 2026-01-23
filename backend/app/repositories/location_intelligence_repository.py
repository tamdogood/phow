"""Repository for location intelligence data operations."""

import uuid
from typing import Any
from datetime import datetime, timedelta
from .base import BaseRepository


class LocationIntelligenceRepository(BaseRepository):
    """Repository for location intelligence data (structured storage)."""

    async def create(
        self,
        geohash: str,
        data_type: str,
        data: dict[str, Any],
        source: str,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        state: str | None = None,
        valid_days: int = 7,
    ) -> dict[str, Any]:
        """Create a new location intelligence record."""
        record_id = str(uuid.uuid4())
        valid_until = datetime.utcnow() + timedelta(days=valid_days)

        result = (
            self.db.table("location_intelligence")
            .insert(
                {
                    "id": record_id,
                    "geohash": geohash,
                    "data_type": data_type,
                    "data": data,
                    "source": source,
                    "location_lat": lat,
                    "location_lng": lng,
                    "city": city,
                    "state": state,
                    "valid_until": valid_until.isoformat(),
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_geohash(
        self,
        geohash: str,
        data_type: str | None = None,
        include_expired: bool = False,
    ) -> list[dict[str, Any]]:
        """Get location intelligence by geohash prefix."""
        query = (
            self.db.table("location_intelligence")
            .select("*")
            .like("geohash", f"{geohash}%")
        )

        if data_type:
            query = query.eq("data_type", data_type)

        if not include_expired:
            query = query.gt("valid_until", datetime.utcnow().isoformat())

        result = query.order("collected_at", desc=True).execute()
        return result.data or []

    async def get_by_city(
        self,
        city: str,
        data_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get location intelligence by city."""
        query = (
            self.db.table("location_intelligence")
            .select("*")
            .ilike("city", f"%{city}%")
            .gt("valid_until", datetime.utcnow().isoformat())
        )

        if data_type:
            query = query.eq("data_type", data_type)

        result = query.order("collected_at", desc=True).limit(limit).execute()
        return result.data or []

    async def upsert(
        self,
        geohash: str,
        data_type: str,
        data: dict[str, Any],
        source: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Upsert location intelligence (update if exists, create if not)."""
        # Check for existing record
        existing = await self.get_by_geohash(geohash, data_type)
        if existing:
            # Update existing
            record = existing[0]
            valid_until = datetime.utcnow() + timedelta(days=kwargs.get("valid_days", 7))
            result = (
                self.db.table("location_intelligence")
                .update(
                    {
                        "data": data,
                        "source": source,
                        "collected_at": datetime.utcnow().isoformat(),
                        "valid_until": valid_until.isoformat(),
                    }
                )
                .eq("id", record["id"])
                .execute()
            )
            return result.data[0] if result.data else {}
        else:
            return await self.create(geohash, data_type, data, source, **kwargs)

    async def delete_expired(self) -> int:
        """Delete expired records. Returns count of deleted records."""
        result = (
            self.db.table("location_intelligence")
            .delete()
            .lt("valid_until", datetime.utcnow().isoformat())
            .execute()
        )
        return len(result.data) if result.data else 0


class DataEmbeddingRepository(BaseRepository):
    """Repository for vector embeddings (RAG semantic search)."""

    async def create(
        self,
        source_type: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        lat: float | None = None,
        lng: float | None = None,
        geohash: str | None = None,
        city: str | None = None,
        expires_days: int = 30,
    ) -> dict[str, Any]:
        """Create a new embedding record."""
        record_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        result = (
            self.db.table("data_embeddings")
            .insert(
                {
                    "id": record_id,
                    "source_type": source_type,
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "location_lat": lat,
                    "location_lng": lng,
                    "geohash": geohash,
                    "city": city,
                    "expires_at": expires_at.isoformat(),
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def semantic_search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        source_types: list[str] | None = None,
        geohash_prefix: str | None = None,
        city: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic similarity search.
        Note: This uses pgvector's cosine similarity via RPC function.
        """
        # Build filter conditions
        filters = {}
        if source_types:
            filters["source_types"] = source_types
        if geohash_prefix:
            filters["geohash_prefix"] = geohash_prefix
        if city:
            filters["city"] = city

        # Call RPC function for vector search (requires Supabase function)
        result = self.db.rpc(
            "match_embeddings",
            {
                "query_embedding": query_embedding,
                "match_count": limit,
                "filter_source_types": source_types,
                "filter_geohash": geohash_prefix,
                "filter_city": city,
            },
        ).execute()

        return result.data or []

    async def delete_expired(self) -> int:
        """Delete expired embeddings."""
        result = (
            self.db.table("data_embeddings")
            .delete()
            .lt("expires_at", datetime.utcnow().isoformat())
            .execute()
        )
        return len(result.data) if result.data else 0


class HealthInspectionRepository(BaseRepository):
    """Repository for health inspection records."""

    async def create(
        self,
        business_name: str,
        address: str,
        city: str,
        state: str,
        score: int | None = None,
        grade: str | None = None,
        inspection_date: str | None = None,
        violations: list[dict] | None = None,
        source_url: str | None = None,
        geohash: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """Create a health inspection record."""
        record_id = str(uuid.uuid4())

        result = (
            self.db.table("health_inspections")
            .insert(
                {
                    "id": record_id,
                    "business_name": business_name,
                    "address": address,
                    "city": city,
                    "state": state,
                    "score": score,
                    "grade": grade,
                    "inspection_date": inspection_date,
                    "violations": violations,
                    "source_url": source_url,
                    "geohash": geohash,
                    "location_lat": lat,
                    "location_lng": lng,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_geohash(
        self, geohash: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get health inspections by geohash prefix."""
        result = (
            self.db.table("health_inspections")
            .select("*")
            .like("geohash", f"{geohash}%")
            .order("inspection_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_by_business(
        self, business_name: str, city: str
    ) -> list[dict[str, Any]]:
        """Get inspection history for a business."""
        result = (
            self.db.table("health_inspections")
            .select("*")
            .ilike("business_name", f"%{business_name}%")
            .ilike("city", f"%{city}%")
            .order("inspection_date", desc=True)
            .execute()
        )
        return result.data or []


class MenuDataRepository(BaseRepository):
    """Repository for menu/pricing data."""

    async def create(
        self,
        business_name: str,
        city: str,
        platform: str,
        items: list[dict],
        business_id: str | None = None,
        address: str | None = None,
        category: str | None = None,
        avg_price: float | None = None,
        price_range: str | None = None,
        geohash: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """Create a menu data record."""
        record_id = str(uuid.uuid4())

        result = (
            self.db.table("menu_data")
            .insert(
                {
                    "id": record_id,
                    "business_name": business_name,
                    "business_id": business_id,
                    "platform": platform,
                    "address": address,
                    "city": city,
                    "category": category,
                    "items": items,
                    "avg_price": avg_price,
                    "price_range": price_range,
                    "geohash": geohash,
                    "location_lat": lat,
                    "location_lng": lng,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_pricing_by_category(
        self, city: str, category: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get menu pricing data by category and city."""
        result = (
            self.db.table("menu_data")
            .select("*")
            .ilike("city", f"%{city}%")
            .ilike("category", f"%{category}%")
            .order("collected_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_by_geohash(
        self, geohash: str, category: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get menu data by geohash."""
        query = (
            self.db.table("menu_data")
            .select("*")
            .like("geohash", f"{geohash}%")
        )

        if category:
            query = query.ilike("category", f"%{category}%")

        result = query.order("collected_at", desc=True).limit(limit).execute()
        return result.data or []


class BusinessHistoryRepository(BaseRepository):
    """Repository for historical business data at locations."""

    async def create(
        self,
        address: str,
        city: str,
        state: str,
        business_name: str,
        business_type: str | None = None,
        opened_date: str | None = None,
        closed_date: str | None = None,
        duration_months: int | None = None,
        closure_reason: str | None = None,
        source: str | None = None,
        geohash: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        """Create a business history record."""
        record_id = str(uuid.uuid4())

        result = (
            self.db.table("business_history")
            .insert(
                {
                    "id": record_id,
                    "address": address,
                    "city": city,
                    "state": state,
                    "business_name": business_name,
                    "business_type": business_type,
                    "opened_date": opened_date,
                    "closed_date": closed_date,
                    "duration_months": duration_months,
                    "closure_reason": closure_reason,
                    "source": source,
                    "geohash": geohash,
                    "location_lat": lat,
                    "location_lng": lng,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {}

    async def get_by_address(
        self, address: str, city: str
    ) -> list[dict[str, Any]]:
        """Get business history for an address."""
        result = (
            self.db.table("business_history")
            .select("*")
            .ilike("address", f"%{address}%")
            .ilike("city", f"%{city}%")
            .order("closed_date", desc=True)
            .execute()
        )
        return result.data or []

    async def get_by_geohash(self, geohash: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get business history by geohash."""
        result = (
            self.db.table("business_history")
            .select("*")
            .like("geohash", f"{geohash}%")
            .order("closed_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_failure_rate(self, geohash: str, business_type: str | None = None) -> dict[str, Any]:
        """Calculate business failure statistics for an area."""
        query = (
            self.db.table("business_history")
            .select("*")
            .like("geohash", f"{geohash}%")
        )

        if business_type:
            query = query.ilike("business_type", f"%{business_type}%")

        result = query.execute()
        records = result.data or []

        if not records:
            return {"total": 0, "closed": 0, "avg_duration_months": None}

        closed = [r for r in records if r.get("closed_date")]
        durations = [r["duration_months"] for r in closed if r.get("duration_months")]

        return {
            "total": len(records),
            "closed": len(closed),
            "failure_rate": round(len(closed) / len(records) * 100, 1) if records else 0,
            "avg_duration_months": round(sum(durations) / len(durations), 1) if durations else None,
        }
