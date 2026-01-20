"""Tests for market analysis service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.market_analysis_service import (
    MarketAnalysisService,
    get_market_analysis_service,
    INDUSTRY_SPENDING_PER_CAPITA,
    MARKET_PARTICIPATION_RATES,
    CAPTURE_RATES,
)


class TestMarketSizeCalculator:
    """Tests for TAM/SAM/SOM calculations."""

    @pytest.fixture
    def service(self):
        return MarketAnalysisService()

    @pytest.fixture
    def mock_demographics(self):
        return {
            "population": {"total": 50000},
            "income": {"median_household": 75000},
            "age_distribution": {
                "median_age": 35,
                "under_18_percent": 22,
                "age_18_34_percent": 28,
                "age_35_plus_percent": 50,
            },
            "education": {"college_plus_percent": 45, "bachelors_plus_percent": 35},
            "housing": {"total_units": 2500, "median_home_value": 400000},
        }

    @pytest.mark.asyncio
    async def test_calculate_market_size_coffee_shop(self, service, mock_demographics):
        """Test market size calculation for coffee shop."""
        with patch.object(
            service, "_get_area_demographics", new_callable=AsyncMock
        ) as mock_demo:
            mock_demo.return_value = mock_demographics

            result = await service.calculate_market_size(
                location={"lat": 47.6062, "lng": -122.3321},
                business_type="coffee shop",
                radius_miles=3.0,
                competitor_count=10,
            )

            assert "tam" in result
            assert "sam" in result
            assert "som" in result
            assert result["tam"]["value"] > 0
            assert result["sam"]["value"] > 0
            assert result["som"]["value"] > 0

            # TAM > SAM > SOM
            assert result["tam"]["value"] >= result["sam"]["value"]
            assert result["sam"]["value"] >= result["som"]["value"]

            # Methodology is included
            assert "methodology" in result
            assert result["methodology"]["naics_code"] == "722515"

    @pytest.mark.asyncio
    async def test_calculate_market_size_gym(self, service, mock_demographics):
        """Test market size for gym (lower participation rate)."""
        with patch.object(
            service, "_get_area_demographics", new_callable=AsyncMock
        ) as mock_demo:
            mock_demo.return_value = mock_demographics

            result = await service.calculate_market_size(
                location={"lat": 47.6062, "lng": -122.3321},
                business_type="gym",
                radius_miles=5.0,
            )

            # Gym has lower participation rate (20% vs 65% for coffee)
            assert result["methodology"]["participation_rate"] == MARKET_PARTICIPATION_RATES.get(
                "713940"
            )
            assert result["methodology"]["naics_code"] == "713940"

    @pytest.mark.asyncio
    async def test_capture_rate_by_competition(self, service, mock_demographics):
        """Test that SOM varies based on competition level."""
        with patch.object(
            service, "_get_area_demographics", new_callable=AsyncMock
        ) as mock_demo:
            mock_demo.return_value = mock_demographics

            # Low competition
            result_low = await service.calculate_market_size(
                location={"lat": 47.6062, "lng": -122.3321},
                business_type="coffee shop",
                radius_miles=3.0,
                competitor_count=3,
            )

            # High competition
            result_high = await service.calculate_market_size(
                location={"lat": 47.6062, "lng": -122.3321},
                business_type="coffee shop",
                radius_miles=3.0,
                competitor_count=25,
            )

            # Lower competition should yield higher SOM
            assert (
                result_low["methodology"]["capture_rate"]
                > result_high["methodology"]["capture_rate"]
            )

    def test_capture_rates_configuration(self, service):
        """Test capture rate thresholds."""
        assert service._get_capture_rate(2) == CAPTURE_RATES["low_competition"]
        assert service._get_capture_rate(10) == CAPTURE_RATES["moderate_competition"]
        assert service._get_capture_rate(20) == CAPTURE_RATES["high_competition"]
        assert service._get_capture_rate(50) == CAPTURE_RATES["very_high_competition"]

    def test_demographic_fit_calculation(self, service):
        """Test demographic fit scoring."""
        demographics = {
            "income": {"median_household": 90000},
            "age_distribution": {"age_18_34_percent": 35},
            "education": {"college_plus_percent": 50},
        }

        # Coffee shops benefit from young, educated demographics
        fit = service._calculate_demographic_fit(demographics, "722515")
        assert fit > 1.0  # Should be above baseline

        # Daycare with low children population
        demographics["age_distribution"]["under_18_percent"] = 10
        fit_daycare = service._calculate_demographic_fit(demographics, "624410")
        assert fit_daycare < 1.0  # Should be below baseline

    def test_confidence_calculation(self, service):
        """Test confidence scoring."""
        # Full data
        full_demo = {
            "population": {"total": 50000},
            "income": {"median_household": 75000},
        }
        conf = service._calculate_confidence(full_demo, has_competitor_data=True)
        assert conf["score"] >= 85
        assert conf["level"] == "high"

        # Minimal data
        minimal_demo = {}
        conf_min = service._calculate_confidence(minimal_demo, has_competitor_data=False)
        assert conf_min["score"] < 85
        assert conf_min["level"] in ["medium", "low"]


class TestMarketGrowthCalculator:
    """Tests for growth rate calculations."""

    @pytest.fixture
    def service(self):
        return MarketAnalysisService()

    @pytest.mark.asyncio
    async def test_calculate_growth_rate(self, service):
        """Test growth rate calculation."""
        with patch.object(
            service.bls_client, "get_industry_employment_trends", new_callable=AsyncMock
        ) as mock_bls:
            mock_bls.return_value = {"cagr_percent": 3.5}

            with patch.object(
                service.fred_client, "get_economic_indicators", new_callable=AsyncMock
            ) as mock_fred:
                mock_fred.return_value = {"gdp": {"value": 25000}}

                result = await service.calculate_growth_rate("722515")

                assert "historical_cagr" in result
                assert "blended_growth_rate" in result
                assert result["historical_cagr"] == 3.5

    @pytest.mark.asyncio
    async def test_project_market_size(self, service):
        """Test market size projections."""
        result = await service.project_market_size(
            current_tam=1000000, growth_rate=5.0, years=5
        )

        assert len(result["projections"]) == 5
        # Year 5 should be ~27.6% higher (1.05^5 - 1)
        assert result["projections"][4]["projected_tam"] > 1270000

        # Each year should be higher than the previous
        for i in range(1, len(result["projections"])):
            assert (
                result["projections"][i]["projected_tam"]
                > result["projections"][i - 1]["projected_tam"]
            )


class TestIndustryProfile:
    """Tests for industry profile building."""

    @pytest.fixture
    def service(self):
        return MarketAnalysisService()

    @pytest.mark.asyncio
    async def test_get_industry_profile(self, service):
        """Test industry profile generation."""
        with patch.object(
            service.bls_client, "get_employment_by_industry", new_callable=AsyncMock
        ) as mock_emp:
            mock_emp.return_value = {"latest_value": 1500000}

            with patch.object(
                service.bls_client, "get_industry_employment_trends", new_callable=AsyncMock
            ) as mock_trends:
                mock_trends.return_value = {"cagr_percent": 2.5}

                with patch.object(
                    service.fred_client, "get_economic_indicators", new_callable=AsyncMock
                ) as mock_fred:
                    mock_fred.return_value = {
                        "unemployment": {"value": 3.8},
                        "consumer_confidence": {"value": 105},
                        "_interpretation": {},
                    }

                    result = await service.get_industry_profile("722515")

                    assert result["naics_code"] == "722515"
                    assert "industry_name" in result
                    assert "employment" in result
                    assert "economic_context" in result


class TestLaborMarketAnalysis:
    """Tests for labor market analysis."""

    @pytest.fixture
    def service(self):
        return MarketAnalysisService()

    @pytest.fixture
    def mock_demographics(self):
        return {
            "population": {"total": 50000},
            "age_distribution": {"age_18_34_percent": 30},
        }

    @pytest.mark.asyncio
    async def test_analyze_labor_market(self, service, mock_demographics):
        """Test labor market analysis."""
        with patch.object(
            service, "_get_area_demographics", new_callable=AsyncMock
        ) as mock_demo:
            mock_demo.return_value = mock_demographics

            with patch.object(
                service.bls_client, "get_wage_data", new_callable=AsyncMock
            ) as mock_wage:
                mock_wage.return_value = {"hourly_mean_wage": 16.50, "annual_mean_wage": 34320}

                with patch.object(
                    service.fred_client, "get_economic_indicators", new_callable=AsyncMock
                ) as mock_fred:
                    mock_fred.return_value = {"unemployment": {"value": 4.2}}

                    result = await service.analyze_labor_market(
                        location={"lat": 47.6062, "lng": -122.3321},
                        business_type="coffee shop",
                    )

                    assert "workforce" in result
                    assert "wages" in result
                    assert "hiring_difficulty" in result
                    assert result["wages"]["hourly_mean"] == 16.50

    def test_hiring_difficulty_tight_market(self, service):
        """Test hiring difficulty in tight labor market."""
        # Low unemployment = harder to hire
        difficulty = service._calculate_hiring_difficulty(3.0, 15.0, "722515")
        assert difficulty > 60

    def test_hiring_difficulty_loose_market(self, service):
        """Test hiring difficulty in loose labor market."""
        # Higher unemployment = easier to hire
        difficulty = service._calculate_hiring_difficulty(7.0, 18.0, "722515")
        assert difficulty < 50


class TestServiceSingleton:
    """Test singleton pattern."""

    def test_singleton_instance(self):
        """Test that get_market_analysis_service returns singleton."""
        service1 = get_market_analysis_service()
        service2 = get_market_analysis_service()
        assert service1 is service2


class TestIndustryDataIntegrity:
    """Tests for industry data completeness."""

    def test_spending_data_exists_for_common_industries(self):
        """Test that spending data exists for common industries."""
        common_codes = ["722515", "722511", "713940", "812112", "445110"]
        for code in common_codes:
            assert code in INDUSTRY_SPENDING_PER_CAPITA, f"Missing spending data for {code}"

    def test_participation_rates_exist_for_common_industries(self):
        """Test that participation rates exist for common industries."""
        common_codes = ["722515", "722511", "713940", "812112"]
        for code in common_codes:
            assert code in MARKET_PARTICIPATION_RATES, f"Missing participation rate for {code}"

    def test_participation_rates_are_valid(self):
        """Test that participation rates are between 0 and 1."""
        for code, rate in MARKET_PARTICIPATION_RATES.items():
            assert 0 < rate <= 1, f"Invalid participation rate for {code}: {rate}"

    def test_capture_rates_are_valid(self):
        """Test that capture rates are reasonable."""
        for level, rate in CAPTURE_RATES.items():
            assert 0 < rate < 1, f"Invalid capture rate for {level}: {rate}"
