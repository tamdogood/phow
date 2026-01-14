import uuid
from typing import Any
from .base import BaseRepository


class BusinessProfileRepository(BaseRepository):
    """Repository for business profile database operations."""

    async def create(
        self,
        session_id: str,
        business_type: str,
        business_name: str | None = None,
        business_description: str | None = None,
        target_customers: str | None = None,
        location_address: str | None = None,
        location_lat: float | None = None,
        location_lng: float | None = None,
        location_place_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new business profile."""
        profile_id = str(uuid.uuid4())
        data = {
            "id": profile_id,
            "session_id": session_id,
            "business_type": business_type,
            "business_name": business_name,
            "business_description": business_description,
            "target_customers": target_customers,
            "location_address": location_address,
            "location_lat": location_lat,
            "location_lng": location_lng,
            "location_place_id": location_place_id,
            "user_id": user_id,
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        result = self.db.table("business_profiles").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_by_id(self, profile_id: str) -> dict[str, Any] | None:
        """Get business profile by ID."""
        result = self.db.table("business_profiles").select("*").eq("id", profile_id).execute()
        return result.data[0] if result.data else None

    async def get_by_session(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get all business profiles for a session."""
        result = (
            self.db.table("business_profiles")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    async def get_latest_by_session(self, session_id: str) -> dict[str, Any] | None:
        """Get the most recent business profile for a session."""
        result = (
            self.db.table("business_profiles")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def update(self, profile_id: str, **kwargs) -> dict[str, Any] | None:
        """Update a business profile."""
        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return await self.get_by_id(profile_id)
        result = (
            self.db.table("business_profiles")
            .update(updates)
            .eq("id", profile_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete(self, profile_id: str) -> bool:
        """Delete a business profile."""
        result = self.db.table("business_profiles").delete().eq("id", profile_id).execute()
        return bool(result.data)


class TrackedCompetitorRepository(BaseRepository):
    """Repository for tracked competitor database operations."""

    async def add_competitor(
        self,
        business_profile_id: str,
        place_id: str,
        name: str,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        rating: float | None = None,
        review_count: int | None = None,
        price_level: int | None = None,
        business_status: str | None = None,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add a tracked competitor."""
        competitor_id = str(uuid.uuid4())
        data = {
            "id": competitor_id,
            "business_profile_id": business_profile_id,
            "place_id": place_id,
            "name": name,
            "address": address,
            "lat": lat,
            "lng": lng,
            "rating": rating,
            "review_count": review_count,
            "price_level": price_level,
            "business_status": business_status,
            "categories": categories,
        }
        data = {k: v for k, v in data.items() if v is not None}
        result = self.db.table("tracked_competitors").upsert(data, on_conflict="business_profile_id,place_id").execute()
        return result.data[0] if result.data else {}

    async def get_competitors(self, business_profile_id: str) -> list[dict[str, Any]]:
        """Get all tracked competitors for a business profile."""
        result = (
            self.db.table("tracked_competitors")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("rating", desc=True)
            .execute()
        )
        return result.data or []

    async def update_competitor(
        self,
        competitor_id: str,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Update a tracked competitor."""
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if strengths is not None:
            updates["strengths"] = strengths
        if weaknesses is not None:
            updates["weaknesses"] = weaknesses
        if not updates:
            return None
        result = (
            self.db.table("tracked_competitors")
            .update(updates)
            .eq("id", competitor_id)
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete_competitor(self, competitor_id: str) -> bool:
        """Delete a tracked competitor."""
        result = self.db.table("tracked_competitors").delete().eq("id", competitor_id).execute()
        return bool(result.data)


class MarketAnalysisRepository(BaseRepository):
    """Repository for market analysis results."""

    async def save_analysis(
        self,
        business_profile_id: str,
        viability_score: int,
        demographics: dict | None = None,
        demand_indicators: dict | None = None,
        competition_saturation: dict | None = None,
        market_size_estimates: dict | None = None,
        risk_factors: dict | None = None,
        opportunities: dict | None = None,
        recommendations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save a market analysis result."""
        analysis_id = str(uuid.uuid4())
        data = {
            "id": analysis_id,
            "business_profile_id": business_profile_id,
            "viability_score": viability_score,
            "demographics": demographics,
            "demand_indicators": demand_indicators,
            "competition_saturation": competition_saturation,
            "market_size_estimates": market_size_estimates,
            "risk_factors": risk_factors,
            "opportunities": opportunities,
            "recommendations": recommendations,
        }
        data = {k: v for k, v in data.items() if v is not None}
        result = self.db.table("market_analyses").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_latest(self, business_profile_id: str) -> dict[str, Any] | None:
        """Get the most recent market analysis for a business profile."""
        result = (
            self.db.table("market_analyses")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    async def get_history(self, business_profile_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get market analysis history for a business profile."""
        result = (
            self.db.table("market_analyses")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []


class CompetitorAnalysisRepository(BaseRepository):
    """Repository for competitor analysis results."""

    async def save_analysis(
        self,
        business_profile_id: str,
        overall_competition_level: str,
        positioning_data: dict | None = None,
        market_gaps: dict | None = None,
        sentiment_summary: dict | None = None,
        pricing_insights: dict | None = None,
        differentiation_suggestions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save a competitor analysis result."""
        analysis_id = str(uuid.uuid4())
        data = {
            "id": analysis_id,
            "business_profile_id": business_profile_id,
            "overall_competition_level": overall_competition_level,
            "positioning_data": positioning_data,
            "market_gaps": market_gaps,
            "sentiment_summary": sentiment_summary,
            "pricing_insights": pricing_insights,
            "differentiation_suggestions": differentiation_suggestions,
        }
        data = {k: v for k, v in data.items() if v is not None}
        result = self.db.table("competitor_analyses").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_latest(self, business_profile_id: str) -> dict[str, Any] | None:
        """Get the most recent competitor analysis for a business profile."""
        result = (
            self.db.table("competitor_analyses")
            .select("*")
            .eq("business_profile_id", business_profile_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
