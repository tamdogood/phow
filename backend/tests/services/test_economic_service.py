"""Tests for economic service."""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.economic_service import (
    EconomicService,
    get_economic_service,
    INDUSTRY_SEASONALITY,
)


class TestEconomicSnapshot:
    """Tests for economic snapshot functionality."""

    @pytest.fixture
    def service(self):
        return EconomicService()

    @pytest.mark.asyncio
    async def test_get_economic_snapshot_national(self, service):
        """Test getting national economic snapshot."""
        with patch.object(
            service.fred_client, "get_economic_indicators", new_callable=AsyncMock
        ) as mock_fred:
            mock_fred.return_value = {
                "unemployment": {"value": 4.0, "date": "2024-01-01", "title": "Unemployment Rate"},
                "consumer_confidence": {"value": 95, "date": "2024-01-01", "title": "Consumer Confidence"},
                "gdp": {"value": 25000, "date": "2024-01-01", "title": "GDP"},
                "_interpretation": {"unemployment": "Healthy labor market"},
            }

            result = await service.get_economic_snapshot()

            assert result["scope"] == "national"
            assert "indicators" in result
            assert "outlook" in result
            assert result["indicators"]["unemployment"]["value"] == 4.0

    @pytest.mark.asyncio
    async def test_get_economic_snapshot_regional(self, service):
        """Test getting regional economic snapshot."""
        with patch.object(
            service.fred_client, "get_economic_indicators", new_callable=AsyncMock
        ) as mock_indicators:
            mock_indicators.return_value = {
                "unemployment": {"value": 4.0},
                "consumer_confidence": {"value": 95},
                "_interpretation": {},
            }

            with patch.object(
                service.fred_client, "get_series", new_callable=AsyncMock
            ) as mock_series:
                mock_series.return_value = {"latest_value": 3.8, "latest_date": "2024-01-01"}

                result = await service.get_economic_snapshot("TX")

                assert result["scope"] == "TX"
                assert "regional" in result

    def test_generate_outlook_favorable(self, service):
        """Test favorable outlook generation."""
        indicators = {
            "unemployment": {"value": 3.5},
            "consumer_confidence": {"value": 105},
        }
        outlook = service._generate_outlook(indicators)

        assert outlook["level"] == "favorable"
        assert outlook["score"] >= 65

    def test_generate_outlook_challenging(self, service):
        """Test challenging outlook generation."""
        indicators = {
            "unemployment": {"value": 7.0},
            "consumer_confidence": {"value": 70},
        }
        outlook = service._generate_outlook(indicators)

        assert outlook["level"] == "challenging"
        assert outlook["score"] < 45


class TestSeasonality:
    """Tests for seasonality patterns."""

    @pytest.fixture
    def service(self):
        return EconomicService()

    def test_get_seasonality_pattern_coffee(self, service):
        """Test getting seasonality for coffee shop."""
        result = service.get_seasonality_pattern("722515")

        assert result["naics_code"] == "722515"
        assert "monthly_indices" in result
        assert len(result["monthly_indices"]) == 12
        assert result["peak_month"]
        assert result["low_month"]

    def test_get_seasonality_pattern_gym(self, service):
        """Test getting seasonality for gym - should have January peak."""
        result = service.get_seasonality_pattern("713940")

        # Gyms typically peak in January (New Year resolutions)
        assert result["peak_month"] == "January"
        assert result["peak_index"] > 1.0

    def test_get_seasonality_pattern_default(self, service):
        """Test default seasonality for unknown code."""
        result = service.get_seasonality_pattern("999999")

        assert result["naics_code"] == "999999"
        assert "monthly_indices" in result

    def test_seasonality_data_validity(self):
        """Test that all seasonality indices are reasonable."""
        for code, pattern in INDUSTRY_SEASONALITY.items():
            for month, index in pattern.items():
                assert 0.5 <= index <= 1.5, f"Index {index} for {code} month {month} out of range"
            # Verify all 12 months present
            assert len(pattern) == 12


class TestEntryTiming:
    """Tests for market entry timing analysis."""

    def test_seasonality_affects_optimal_months(self):
        """Test that seasonality pattern affects optimal month recommendations."""
        service = EconomicService()

        # Gym pattern has January peak, so optimal months should be before that
        pattern = service.get_seasonality_pattern("713940")
        assert pattern["peak_month"] == "January"

        # Coffee shop pattern - peak is in December
        pattern_coffee = service.get_seasonality_pattern("722515")
        assert pattern_coffee["peak_index"] > 1.0

    def test_outlook_summary_generation(self):
        """Test outlook summary generation."""
        service = EconomicService()

        favorable_summary = service._get_outlook_summary("favorable")
        assert "favorable" in favorable_summary.lower()

        challenging_summary = service._get_outlook_summary("challenging")
        assert "challeng" in challenging_summary.lower()

        neutral_summary = service._get_outlook_summary("neutral")
        assert "stable" in neutral_summary.lower()


class TestConsumerSpending:
    """Tests for consumer spending trends."""

    @pytest.fixture
    def service(self):
        return EconomicService()

    @pytest.mark.asyncio
    async def test_get_consumer_spending_trends(self, service):
        """Test getting consumer spending trends."""
        with patch.object(
            service.fred_client, "get_series", new_callable=AsyncMock
        ) as mock_series:
            mock_series.return_value = {
                "latest_value": 500000,
                "latest_date": "2024-01-01",
                "observations": [
                    {"value": 510000},
                    {"value": 505000},
                    {"value": 500000},
                    {"value": 495000},
                    {"value": 490000},
                    {"value": 485000},
                    {"value": 480000},
                    {"value": 475000},
                    {"value": 470000},
                    {"value": 465000},
                    {"value": 460000},
                    {"value": 455000},
                ],
            }

            result = await service.get_consumer_spending_trends()

            assert "latest_value" in result
            assert "trend" in result
            assert "interpretation" in result


class TestServiceSingleton:
    """Test singleton pattern."""

    def test_singleton_instance(self):
        """Test that get_economic_service returns singleton."""
        service1 = get_economic_service()
        service2 = get_economic_service()
        assert service1 is service2


class TestSeasonalityDataIntegrity:
    """Tests for seasonality data completeness."""

    def test_common_industries_have_seasonality(self):
        """Test that common industries have seasonality data."""
        common_codes = ["722515", "722511", "713940", "812112"]
        for code in common_codes:
            assert code in INDUSTRY_SEASONALITY, f"Missing seasonality for {code}"

    def test_seasonality_sums_to_12(self):
        """Test that monthly indices average to ~1.0."""
        for code, pattern in INDUSTRY_SEASONALITY.items():
            avg = sum(pattern.values()) / 12
            # Average should be close to 1.0 (within 0.1)
            assert 0.9 <= avg <= 1.1, f"Average index for {code} is {avg}"
