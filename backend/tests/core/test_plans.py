"""Tests for the pure plan/entitlement logic (app/core/plans.py)."""

from app.core import plans


class TestPlanResolution:
    def test_unknown_defaults_to_free(self):
        assert plans.plan_name(None) == "free"
        assert plans.plan_name("enterprise") == "free"
        assert plans.get_plan("bogus")["label"] == "Starter"

    def test_known_plans_resolve(self):
        assert plans.plan_name("PRO") == "pro"
        assert plans.get_plan("multi")["label"] == "Multi-Unit"


class TestFeatures:
    def test_free_lacks_premium_features(self):
        assert plans.has_feature("free", "daily_brief") is False
        assert plans.has_feature("free", "cost_radar") is False

    def test_pro_has_premium_features(self):
        assert plans.has_feature("pro", "daily_brief") is True
        assert plans.has_feature("pro", "review_autopilot") is True

    def test_unknown_feature_is_false(self):
        assert plans.has_feature("pro", "time_travel") is False


class TestLimits:
    def test_free_competitor_cap(self):
        assert plans.limit("free", "tracked_competitors") == 3
        assert plans.within_limit("free", "tracked_competitors", 2) is True
        assert plans.within_limit("free", "tracked_competitors", 3) is False
        assert plans.remaining("free", "tracked_competitors", 2) == 1

    def test_unlimited_sentinel(self):
        assert plans.limit("pro", "scenario_runs_monthly") == plans.UNLIMITED
        assert plans.within_limit("pro", "scenario_runs_monthly", 9999) is True
        assert plans.remaining("pro", "scenario_runs_monthly", 9999) == plans.UNLIMITED


class TestEntitlementsShape:
    def test_entitlements_payload(self):
        ent = plans.entitlements("pro")
        assert ent["plan"] == "pro"
        assert ent["price_monthly"] == 59
        assert set(ent) >= {"plan", "label", "price_monthly", "limits", "features"}

    def test_public_plans_lists_all_tiers(self):
        ids = {p["id"] for p in plans.public_plans()}
        assert ids == {"free", "pro", "multi"}
