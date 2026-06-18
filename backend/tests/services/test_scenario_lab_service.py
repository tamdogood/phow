"""Tests for ScenarioLabService — the deterministic what-if margin calculator."""

from app.services.scenario_lab_service import ScenarioLabService, DEFAULTS


class TestBaseline:
    def test_defaults_produce_sane_economics(self):
        out = ScenarioLabService.run({}, {})
        base = out["base"]
        # 18 * 120 * 26 = 56,160/mo
        assert base["monthly_revenue"] == 56160.0
        assert base["monthly_profit"] > 0
        assert base["break_even_covers_per_day"] is not None
        # no overrides => scenario == base => zero deltas
        assert out["deltas"]["monthly_profit"] == 0.0

    def test_owner_inputs_override_defaults(self):
        out = ScenarioLabService.run({"avg_check": 9.0}, {})
        assert out["inputs"]["avg_check"] == 9.0
        assert out["inputs"]["daily_covers"] == DEFAULTS["daily_covers"]


class TestLevers:
    def test_price_increase_lifts_revenue_profit_and_margin(self):
        out = ScenarioLabService.run({}, {"price_change_pct": 0.10})
        assert out["deltas"]["monthly_revenue"] > 0
        assert out["deltas"]["monthly_profit"] > 0
        assert out["deltas"]["profit_margin_pct"] > 0
        # higher price => fewer covers needed to break even
        assert (
            out["scenario"]["break_even_covers_per_day"] < out["base"]["break_even_covers_per_day"]
        )

    def test_rent_hike_cuts_profit_one_for_one_and_raises_break_even(self):
        out = ScenarioLabService.run({}, {"monthly_fixed_delta": 3000})
        # revenue unchanged; profit drops by exactly the rent delta
        assert out["deltas"]["monthly_revenue"] == 0.0
        assert out["deltas"]["monthly_profit"] == -3000.0
        assert out["deltas"]["break_even_covers_per_day"] > 0

    def test_food_cost_spike_compresses_margin(self):
        out = ScenarioLabService.run({}, {"food_cost_pct_delta": 0.10})
        assert out["deltas"]["profit_margin_pct"] < 0
        assert out["scenario"]["variable_cost_pct"] > out["base"]["variable_cost_pct"]

    def test_more_covers_lifts_revenue(self):
        out = ScenarioLabService.run({}, {"covers_change_pct": 0.20})
        assert out["deltas"]["monthly_revenue"] > 0


class TestInsights:
    def test_profit_to_loss_is_flagged(self):
        out = ScenarioLabService.run({}, {"food_cost_pct_delta": 0.15})
        assert out["scenario"]["monthly_profit"] < 0
        assert any("loss" in i.lower() for i in out["insights"])

    def test_low_margin_warns_below_survival_line(self):
        # baseline ~3% margin already sits below the 5% survival line
        out = ScenarioLabService.run({}, {})
        assert any("survival line" in i for i in out["insights"])
