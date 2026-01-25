"""Service for running dashboard auto-analysis."""

from typing import Any
from supabase import Client
from .business_profile_service import BusinessProfileService
from ..tools.market_validator.agent_tools import calculate_market_viability
from ..tools.competitor_analyzer.agent_tools import find_competitors, analyze_competitor_reviews
from ..core.logging import get_logger

logger = get_logger("analysis_service")


class AnalysisService:
    """Service for running automated market and competitor analysis."""

    def __init__(self, db: Client):
        self.profile_service = BusinessProfileService(db)

    async def run_market_analysis(
        self,
        address: str,
        business_type: str,
        profile_id: str,
    ) -> dict[str, Any] | None:
        """Run market viability analysis and save results."""
        logger.info("Running market analysis", address=address, business_type=business_type)

        try:
            result = await calculate_market_viability.ainvoke(
                {
                    "address": address,
                    "business_type": business_type,
                }
            )

            if "error" in result:
                logger.error("Market analysis error", error=result["error"])
                return None

            # Save analysis to database
            await self.profile_service.save_market_analysis(
                profile_id=profile_id,
                viability_score=result.get("viability_score", 0),
                demographics=result.get("demographics_summary"),
                competition_saturation=result.get("competition_summary"),
                risk_factors=result.get("risk_factors"),
                opportunities=result.get("opportunities"),
                recommendations=result.get("recommendations"),
            )

            return result
        except Exception as e:
            logger.error("Market analysis failed", error=str(e))
            return None

    async def run_competitor_analysis(
        self,
        address: str,
        business_type: str,
        profile_id: str,
    ) -> dict[str, Any] | None:
        """Run competitor analysis and save results."""
        logger.info("Running competitor analysis", address=address, business_type=business_type)

        try:
            # Find competitors
            competitors_result = await find_competitors.ainvoke(
                {
                    "address": address,
                    "business_type": business_type,
                }
            )

            if "error" in competitors_result:
                logger.error("Competitor search error", error=competitors_result["error"])
                return None

            # Analyze reviews for insights
            review_analysis = await analyze_competitor_reviews.ainvoke(
                {
                    "address": address,
                    "business_type": business_type,
                }
            )

            # Determine competition level
            competitor_count = competitors_result.get("total_found", 0)
            if competitor_count == 0:
                competition_level = "None"
            elif competitor_count <= 3:
                competition_level = "Low"
            elif competitor_count <= 7:
                competition_level = "Moderate"
            elif competitor_count <= 12:
                competition_level = "High"
            else:
                competition_level = "Very High"

            # Save competitors
            for comp in competitors_result.get("competitors", [])[:10]:
                place_id = comp.get("place_id") or comp.get("name", "").lower().replace(" ", "_")
                await self.profile_service.add_competitor(
                    profile_id=profile_id,
                    place_id=place_id,
                    name=comp.get("name", "Unknown"),
                    address=comp.get("address"),
                    rating=comp.get("rating"),
                    review_count=comp.get("review_count"),
                    price_level=comp.get("price_level"),
                )

            # Extract insights
            insights = (
                review_analysis.get("insights", {}) if not review_analysis.get("error") else {}
            )

            # Save competitor analysis summary
            await self.profile_service.save_competitor_analysis(
                profile_id=profile_id,
                overall_competition_level=competition_level,
                market_gaps={
                    "opportunities": insights.get("opportunities", []),
                },
                sentiment_summary={
                    "positive_themes": insights.get("strengths", []),
                    "negative_themes": insights.get("weaknesses", []),
                },
                differentiation_suggestions=insights.get("opportunities", []),
            )

            return {
                "competition_level": competition_level,
                "competitors_found": competitor_count,
                "insights": insights,
            }
        except Exception as e:
            logger.error("Competitor analysis failed", error=str(e))
            return None

    async def analyze_if_needed(
        self,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Check if analysis exists for profile, run if not."""
        # Get business profile
        profile = None
        if user_id:
            profile = await self.profile_service.get_profile_by_user(user_id)
        if not profile and session_id:
            profile = await self.profile_service.get_profile(session_id)

        if not profile:
            return {"error": "No business profile found", "analyzed": False}

        profile_id = profile["id"]
        address = profile.get("location_address")
        business_type = profile.get("business_type")

        if not address:
            return {"error": "No address in business profile", "analyzed": False}

        # Check existing analyses
        existing_market = await self.profile_service.get_latest_market_analysis(profile_id)
        existing_competitor = await self.profile_service.get_latest_competitor_analysis(profile_id)

        results = {"analyzed": False, "market": None, "competitors": None}

        # Run market analysis if needed
        if not existing_market:
            results["market"] = await self.run_market_analysis(address, business_type, profile_id)
            results["analyzed"] = True
        else:
            results["market"] = "existing"

        # Run competitor analysis if needed
        if not existing_competitor:
            results["competitors"] = await self.run_competitor_analysis(
                address, business_type, profile_id
            )
            results["analyzed"] = True
        else:
            results["competitors"] = "existing"

        return results
