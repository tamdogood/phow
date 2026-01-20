"""Tests for competitive analysis service."""

import pytest
from app.services.competitive_analysis_service import (
    CompetitiveAnalysisService,
    get_competitive_analysis_service,
)


class TestSWOTAnalysis:
    """Tests for SWOT analysis functionality."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.fixture
    def sample_market_data(self):
        return {
            "competitors": [
                {"name": "Cafe A", "rating": 4.5, "review_count": 200, "price_level": 2},
                {"name": "Cafe B", "rating": 4.0, "review_count": 150, "price_level": 2},
                {"name": "Cafe C", "rating": 3.5, "review_count": 50, "price_level": 1},
            ],
            "demographics": {
                "total_population": 75000,
                "median_income": 85000,
                "age_distribution": {"18-34": 35, "35-54": 30, "55+": 35},
            },
            "foot_traffic": {"score": 75},
            "economic": {"outlook": {"level": "favorable"}},
            "trends": {"trend_direction": "growing", "employment_growth_rate": 3.5},
            "positioning": {"market_gaps": ["Premium segment has room"]},
        }

    @pytest.mark.asyncio
    async def test_generate_swot_basic(self, service, sample_market_data):
        """Test basic SWOT generation."""
        location = {"address": "123 Main St, Seattle, WA", "lat": 47.6, "lng": -122.3}

        result = await service.generate_swot(location, "coffee shop", sample_market_data)

        assert "strengths" in result
        assert "weaknesses" in result
        assert "opportunities" in result
        assert "threats" in result
        assert "assessment" in result
        assert result["business_type"] == "coffee shop"

    @pytest.mark.asyncio
    async def test_swot_identifies_population_strength(self, service, sample_market_data):
        """Test that large population is identified as strength."""
        location = {"address": "Test Address"}

        result = await service.generate_swot(location, "coffee shop", sample_market_data)

        strength_factors = [s["factor"] for s in result["strengths"]]
        assert any("population" in f.lower() for f in strength_factors)

    @pytest.mark.asyncio
    async def test_swot_identifies_income_strength(self, service, sample_market_data):
        """Test that high income is identified as strength."""
        location = {"address": "Test Address"}

        result = await service.generate_swot(location, "coffee shop", sample_market_data)

        strength_factors = [s["factor"] for s in result["strengths"]]
        assert any("income" in f.lower() for f in strength_factors)

    @pytest.mark.asyncio
    async def test_swot_identifies_growing_industry_opportunity(self, service, sample_market_data):
        """Test that growing industry is identified as opportunity."""
        location = {"address": "Test Address"}

        result = await service.generate_swot(location, "coffee shop", sample_market_data)

        opp_factors = [o["factor"] for o in result["opportunities"]]
        assert any("growing" in f.lower() for f in opp_factors)

    @pytest.mark.asyncio
    async def test_swot_assessment_scoring(self, service, sample_market_data):
        """Test SWOT assessment scoring."""
        location = {"address": "Test Address"}

        result = await service.generate_swot(location, "coffee shop", sample_market_data)

        assessment = result["assessment"]
        assert "score" in assessment
        assert 0 <= assessment["score"] <= 100
        assert assessment["level"] in ["favorable", "neutral", "challenging"]
        assert "recommendation" in assessment


class TestPortersFiveForces:
    """Tests for Porter's Five Forces analysis."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.fixture
    def sample_market_data(self):
        return {
            "competitors": [
                {"name": "Comp A", "rating": 4.5, "review_count": 300},
                {"name": "Comp B", "rating": 4.0, "review_count": 150},
                {"name": "Comp C", "rating": 3.8, "review_count": 100},
                {"name": "Comp D", "rating": 4.2, "review_count": 75},
            ],
            "demographics": {"total_population": 50000},
            "trends": {"trend_direction": "growing"},
        }

    @pytest.mark.asyncio
    async def test_five_forces_basic(self, service, sample_market_data):
        """Test basic Five Forces analysis."""
        location = {"address": "Test Address"}

        result = await service.analyze_five_forces(
            "coffee shop", location, sample_market_data
        )

        assert "forces" in result
        forces = result["forces"]
        assert "competitive_rivalry" in forces
        assert "supplier_power" in forces
        assert "buyer_power" in forces
        assert "threat_of_substitutes" in forces
        assert "threat_of_new_entrants" in forces

    @pytest.mark.asyncio
    async def test_five_forces_scores(self, service, sample_market_data):
        """Test that each force has proper scoring."""
        location = {"address": "Test Address"}

        result = await service.analyze_five_forces(
            "coffee shop", location, sample_market_data
        )

        for force_name, force_data in result["forces"].items():
            assert "score" in force_data
            assert 0 <= force_data["score"] <= 100
            assert "level" in force_data
            assert force_data["level"] in ["low", "medium", "high"]
            assert "rationale" in force_data

    @pytest.mark.asyncio
    async def test_five_forces_overall_assessment(self, service, sample_market_data):
        """Test overall industry attractiveness assessment."""
        location = {"address": "Test Address"}

        result = await service.analyze_five_forces(
            "coffee shop", location, sample_market_data
        )

        overall = result["overall"]
        assert "attractiveness_score" in overall
        assert 0 <= overall["attractiveness_score"] <= 100
        assert overall["level"] in ["attractive", "moderate", "challenging"]


class TestMarketShareEstimation:
    """Tests for market share estimation."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.fixture
    def sample_competitors(self):
        return [
            {"name": "Leader Inc", "rating": 4.8, "review_count": 500, "price_level": 3},
            {"name": "Runner Up", "rating": 4.5, "review_count": 200, "price_level": 2},
            {"name": "Small Player", "rating": 4.0, "review_count": 50, "price_level": 2},
        ]

    def test_estimate_market_shares(self, service, sample_competitors):
        """Test market share estimation."""
        result = service.estimate_market_shares(sample_competitors)

        assert "shares" in result
        assert len(result["shares"]) == 3
        assert result["shares"][0]["name"] == "Leader Inc"  # Highest share

        # Shares should sum to 100
        total_share = sum(s["share_percent"] for s in result["shares"])
        assert abs(total_share - 100) < 0.5  # Allow small rounding error

    def test_market_leader_identification(self, service, sample_competitors):
        """Test market leader identification."""
        result = service.estimate_market_shares(sample_competitors)

        leader = result["market_leader"]
        assert leader["name"] == "Leader Inc"

    def test_market_concentration(self, service, sample_competitors):
        """Test market concentration analysis."""
        result = service.estimate_market_shares(sample_competitors)

        concentration = result["concentration"]
        assert "top_3_share" in concentration
        assert concentration["level"] in ["concentrated", "moderate", "fragmented"]

    def test_empty_competitors(self, service):
        """Test with empty competitors list."""
        result = service.estimate_market_shares([])
        assert "error" in result


class TestPricingAnalysis:
    """Tests for pricing landscape analysis."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.fixture
    def sample_competitors(self):
        return [
            {"name": "Premium Place", "rating": 4.8, "price_level": 3, "review_count": 200},
            {"name": "Value Shop", "rating": 4.2, "yelp_price": "$$", "review_count": 150},
            {"name": "Budget Spot", "rating": 3.8, "price_level": 1, "review_count": 100},
            {"name": "Mid Range", "rating": 4.0, "price_level": 2, "review_count": 80},
        ]

    def test_analyze_pricing_landscape(self, service, sample_competitors):
        """Test pricing landscape analysis."""
        result = service.analyze_pricing_landscape(sample_competitors)

        assert "distribution" in result
        assert "$" in result["distribution"]
        assert "$$" in result["distribution"]
        assert "$$$" in result["distribution"]
        assert "dominant_tier" in result
        assert "recommendation" in result

    def test_pricing_gaps_identification(self, service, sample_competitors):
        """Test that pricing gaps are identified."""
        result = service.analyze_pricing_landscape(sample_competitors)

        assert "pricing_gaps" in result
        # With our sample data, luxury segment should be a gap
        assert any("luxury" in gap.lower() or "$$$$" in gap for gap in result["pricing_gaps"])

    def test_price_string_conversion(self, service):
        """Test Yelp price string to level conversion."""
        assert service._price_string_to_level("$") == 1
        assert service._price_string_to_level("$$") == 2
        assert service._price_string_to_level("$$$") == 3
        assert service._price_string_to_level("$$$$") == 4
        assert service._price_string_to_level(None) is None


class TestBenchmarking:
    """Tests for competitor benchmarking."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.fixture
    def sample_competitors(self):
        return [
            {"name": "Top Dog", "rating": 4.7, "review_count": 600, "price_level": 3},
            {"name": "Solid Choice", "rating": 4.3, "review_count": 200, "price_level": 2},
            {"name": "New Kid", "rating": 4.0, "review_count": 30, "price_level": 2},
        ]

    def test_benchmark_against_competitors(self, service, sample_competitors):
        """Test benchmarking analysis."""
        business_profile = {
            "name": "My New Business",
            "price_level": 2,
            "target_quality": "high",
        }

        result = service.benchmark_against_competitors(business_profile, sample_competitors)

        assert "benchmarks" in result
        assert "avg_rating" in result["benchmarks"]
        assert "avg_review_count" in result["benchmarks"]
        assert "competitive_advantages" in result
        assert "competitive_gaps" in result
        assert "recommendations" in result

    def test_benchmarks_calculation(self, service, sample_competitors):
        """Test benchmark calculations are correct."""
        business_profile = {"price_level": 2}

        result = service.benchmark_against_competitors(business_profile, sample_competitors)

        benchmarks = result["benchmarks"]
        # Average rating should be (4.7 + 4.3 + 4.0) / 3 = 4.33
        assert abs(benchmarks["avg_rating"] - 4.33) < 0.1
        # Top rating should be 4.7
        assert benchmarks["top_rating"] == 4.7


class TestServiceSingleton:
    """Test singleton pattern."""

    def test_singleton_instance(self):
        """Test that get_competitive_analysis_service returns singleton."""
        service1 = get_competitive_analysis_service()
        service2 = get_competitive_analysis_service()
        assert service1 is service2


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def service(self):
        return CompetitiveAnalysisService()

    @pytest.mark.asyncio
    async def test_swot_with_minimal_data(self, service):
        """Test SWOT with minimal market data."""
        location = {"address": "Test"}
        market_data = {"competitors": []}

        result = await service.generate_swot(location, "cafe", market_data)

        # Should still produce valid output
        assert "strengths" in result
        assert "weaknesses" in result
        assert len(result["strengths"]) >= 1
        assert len(result["weaknesses"]) >= 1

    @pytest.mark.asyncio
    async def test_five_forces_with_no_competitors(self, service):
        """Test Five Forces with no competitors."""
        location = {"address": "Test"}
        market_data = {"competitors": [], "demographics": {}, "trends": {}}

        result = await service.analyze_five_forces("restaurant", location, market_data)

        # Should still produce valid output
        assert "forces" in result
        assert "overall" in result

    def test_market_shares_with_missing_data(self, service):
        """Test market share estimation with incomplete competitor data."""
        competitors = [
            {"name": "A"},  # Missing rating, review_count
            {"name": "B", "rating": 4.0},  # Missing review_count
            {"name": "C", "review_count": 100},  # Missing rating
        ]

        result = service.estimate_market_shares(competitors)

        # Should handle gracefully
        assert "shares" in result
        assert len(result["shares"]) == 3
