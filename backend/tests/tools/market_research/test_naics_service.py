"""Tests for NAICS code service."""

import pytest
from app.tools.market_research.naics_service import NAICSService, get_naics_service


class TestNAICSService:
    """Tests for NAICSService."""

    @pytest.fixture
    def service(self):
        return NAICSService()

    def test_lookup_code_exists(self, service):
        """Test looking up a valid NAICS code."""
        result = service.lookup_code("722515")
        assert result is not None
        assert result["code"] == "722515"
        assert "coffee" in result["title"].lower() or "snack" in result["title"].lower()

    def test_lookup_code_not_exists(self, service):
        """Test looking up an invalid NAICS code."""
        result = service.lookup_code("999999")
        assert result is None

    def test_search_by_keyword_coffee(self, service):
        """Test searching for coffee-related codes."""
        results = service.search_by_keyword("coffee")
        assert len(results) > 0
        assert any("722515" in r["code"] for r in results)

    def test_search_by_keyword_restaurant(self, service):
        """Test searching for restaurant codes."""
        results = service.search_by_keyword("restaurant")
        assert len(results) > 0
        codes = [r["code"] for r in results]
        assert any(c in ["722511", "722513"] for c in codes)

    def test_search_by_keyword_limit(self, service):
        """Test search result limiting."""
        results = service.search_by_keyword("store", limit=3)
        assert len(results) <= 3

    def test_map_business_type_direct(self, service):
        """Test direct business type mapping."""
        codes = service.map_business_type("coffee shop")
        assert "722515" in codes

    def test_map_business_type_gym(self, service):
        """Test gym business type mapping."""
        codes = service.map_business_type("gym")
        assert "713940" in codes

    def test_map_business_type_salon(self, service):
        """Test salon business type mapping."""
        codes = service.map_business_type("hair salon")
        assert "812112" in codes

    def test_map_business_type_partial_match(self, service):
        """Test partial match business type mapping."""
        codes = service.map_business_type("coffee")
        assert len(codes) > 0

    def test_get_parent_industry(self, service):
        """Test getting parent industry."""
        parent = service.get_parent_industry("722515")
        assert parent is not None
        assert parent["code"] in ["7225", "722", "72"]

    def test_get_parent_industry_top_level(self, service):
        """Test getting parent for top-level code."""
        parent = service.get_parent_industry("72")
        assert parent is None

    def test_get_related_industries(self, service):
        """Test getting related industries."""
        related = service.get_related_industries("722511")
        assert len(related) > 0
        # All should be in same sector (72) and same length
        for r in related:
            assert r["code"].startswith("72")
            assert len(r["code"]) == 6

    def test_get_industry_hierarchy(self, service):
        """Test getting full industry hierarchy."""
        hierarchy = service.get_industry_hierarchy("722515")
        assert len(hierarchy) > 0
        # Should go from broad to specific
        assert hierarchy[0]["code"] == "72"
        assert hierarchy[-1]["code"] == "722515"

    def test_singleton_instance(self):
        """Test that get_naics_service returns singleton."""
        service1 = get_naics_service()
        service2 = get_naics_service()
        assert service1 is service2


class TestNAICSDataIntegrity:
    """Tests for NAICS data integrity."""

    @pytest.fixture
    def service(self):
        return NAICSService()

    def test_all_codes_have_required_fields(self, service):
        """Test that all codes have required fields."""
        for code, info in service.codes.items():
            assert "code" in info
            assert "title" in info
            assert info["code"] == code

    def test_all_mappings_point_to_valid_codes(self, service):
        """Test that all business type mappings point to valid codes."""
        for business_type, codes in service.mappings.items():
            for code in codes:
                assert code in service.codes, f"Mapping '{business_type}' points to invalid code: {code}"

    def test_common_business_types_mapped(self, service):
        """Test that common business types are mapped."""
        common_types = [
            "coffee shop", "restaurant", "gym", "salon", "bakery",
            "bar", "pet store", "daycare", "dry cleaner"
        ]
        for bt in common_types:
            codes = service.map_business_type(bt)
            assert len(codes) > 0, f"Business type '{bt}' has no mappings"
