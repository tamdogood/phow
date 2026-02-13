"""Service for managing business profiles and related data."""

from typing import Any
from supabase import Client
from ..repositories.business_profile_repository import (
    BusinessProfileRepository,
    TrackedCompetitorRepository,
    MarketAnalysisRepository,
    CompetitorAnalysisRepository,
)
from ..tools.location_scout.google_maps import GoogleMapsClient
from ..core.logging import get_logger

logger = get_logger("business_profile")


class BusinessProfileService:
    """Service for business profile management."""

    def __init__(self, db: Client):
        self.profile_repo = BusinessProfileRepository(db)
        self.competitor_repo = TrackedCompetitorRepository(db)
        self.market_repo = MarketAnalysisRepository(db)
        self.competitor_analysis_repo = CompetitorAnalysisRepository(db)
        self.maps = GoogleMapsClient()

    async def _geocode_address(self, address: str) -> tuple[float | None, float | None, str | None]:
        """Geocode an address, returning (lat, lng, place_id) or (None, None, None)."""
        try:
            geo = await self.maps.geocode(address)
            if geo:
                return geo["lat"], geo["lng"], geo.get("place_id")
        except Exception:
            logger.warning("Geocoding failed for address", address=address)
        return None, None, None

    async def create_or_update_profile(
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
        """Create a new business profile or update existing one for session/user."""
        # Geocode address if coordinates not provided
        if location_address and not (location_lat and location_lng):
            location_lat, location_lng, location_place_id = await self._geocode_address(
                location_address
            )

        # Check if profile already exists - try user_id first, then session_id
        existing = None
        if user_id:
            existing = await self.profile_repo.get_latest_by_user(user_id)
        if not existing:
            existing = await self.profile_repo.get_latest_by_session(session_id)

        if existing:
            # Update existing profile
            logger.info("Updating existing business profile", profile_id=existing["id"])
            result = await self.profile_repo.update(
                existing["id"],
                business_type=business_type,
                business_name=business_name,
                business_description=business_description,
                target_customers=target_customers,
                location_address=location_address,
                location_lat=location_lat,
                location_lng=location_lng,
                location_place_id=location_place_id,
                user_id=user_id,
            )
            return result or existing

        # Create new profile
        logger.info(
            "Creating new business profile",
            session_id=session_id,
            business_type=business_type,
        )
        return await self.profile_repo.create(
            session_id=session_id,
            business_type=business_type,
            business_name=business_name,
            business_description=business_description,
            target_customers=target_customers,
            location_address=location_address,
            location_lat=location_lat,
            location_lng=location_lng,
            location_place_id=location_place_id,
            user_id=user_id,
        )

    async def get_profile(self, session_id: str) -> dict[str, Any] | None:
        """Get the current business profile for a session."""
        return await self.profile_repo.get_latest_by_session(session_id)

    async def get_profile_by_user(self, user_id: str) -> dict[str, Any] | None:
        """Get the current business profile for a user."""
        return await self.profile_repo.get_latest_by_user(user_id)

    async def get_profile_by_id(self, profile_id: str) -> dict[str, Any] | None:
        """Get a business profile by ID."""
        return await self.profile_repo.get_by_id(profile_id)

    async def add_competitor(
        self,
        profile_id: str,
        place_id: str,
        name: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Add a tracked competitor to a business profile."""
        logger.info("Adding competitor", profile_id=profile_id, competitor_name=name)
        return await self.competitor_repo.add_competitor(
            business_profile_id=profile_id,
            place_id=place_id,
            name=name,
            **kwargs,
        )

    async def get_competitors(self, profile_id: str) -> list[dict[str, Any]]:
        """Get all tracked competitors for a business profile."""
        return await self.competitor_repo.get_competitors(profile_id)

    async def update_competitor_insights(
        self,
        competitor_id: str,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Update competitor strengths and weaknesses from analysis."""
        return await self.competitor_repo.update_competitor(
            competitor_id=competitor_id,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    async def save_market_analysis(
        self,
        profile_id: str,
        viability_score: int,
        demographics: dict | None = None,
        demand_indicators: dict | None = None,
        competition_saturation: dict | None = None,
        market_size_estimates: dict | None = None,
        risk_factors: dict | None = None,
        opportunities: dict | None = None,
        recommendations: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save market analysis results for a business profile."""
        logger.info(
            "Saving market analysis",
            profile_id=profile_id,
            viability_score=viability_score,
        )
        return await self.market_repo.save_analysis(
            business_profile_id=profile_id,
            viability_score=viability_score,
            demographics=demographics,
            demand_indicators=demand_indicators,
            competition_saturation=competition_saturation,
            market_size_estimates=market_size_estimates,
            risk_factors=risk_factors,
            opportunities=opportunities,
            recommendations=recommendations,
        )

    async def get_latest_market_analysis(self, profile_id: str) -> dict[str, Any] | None:
        """Get the most recent market analysis for a business profile."""
        return await self.market_repo.get_latest(profile_id)

    async def save_competitor_analysis(
        self,
        profile_id: str,
        overall_competition_level: str,
        positioning_data: dict | None = None,
        market_gaps: dict | None = None,
        sentiment_summary: dict | None = None,
        pricing_insights: dict | None = None,
        differentiation_suggestions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Save competitor analysis results for a business profile."""
        logger.info(
            "Saving competitor analysis",
            profile_id=profile_id,
            competition_level=overall_competition_level,
        )
        return await self.competitor_analysis_repo.save_analysis(
            business_profile_id=profile_id,
            overall_competition_level=overall_competition_level,
            positioning_data=positioning_data,
            market_gaps=market_gaps,
            sentiment_summary=sentiment_summary,
            pricing_insights=pricing_insights,
            differentiation_suggestions=differentiation_suggestions,
        )

    async def get_latest_competitor_analysis(self, profile_id: str) -> dict[str, Any] | None:
        """Get the most recent competitor analysis for a business profile."""
        return await self.competitor_analysis_repo.get_latest(profile_id)

    async def get_full_profile_context(self, session_id: str) -> dict[str, Any] | None:
        """Get complete business profile with all related data."""
        profile = await self.get_profile(session_id)
        if not profile:
            return None

        profile_id = profile["id"]

        # Get related data in parallel would be ideal, but keeping it simple
        competitors = await self.get_competitors(profile_id)
        market_analysis = await self.get_latest_market_analysis(profile_id)
        competitor_analysis = await self.get_latest_competitor_analysis(profile_id)

        return {
            "profile": profile,
            "competitors": competitors,
            "market_analysis": market_analysis,
            "competitor_analysis": competitor_analysis,
        }
