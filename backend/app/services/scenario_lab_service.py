"""Scenario Lab — a transparent what-if calculator for F&B unit economics.

Answers the owner's real margin questions ("raise prices 5%? rent +$2k? food cost +10%?")
with profit, margin, and break-even impact. Pure and deterministic — no LLM, no network —
so it's fully testable and instant. Levers are applied to a baseline; missing baseline
fields fall back to sensible F&B defaults the owner can override.
"""

from typing import Any

# Reasonable single-location F&B defaults (owner overrides any of these).
DEFAULTS: dict[str, float] = {
    "avg_check": 18.0,
    "daily_covers": 120.0,
    "days_open_per_month": 26.0,
    "food_cost_pct": 0.30,
    "labor_pct": 0.30,
    "other_variable_pct": 0.05,  # card fees, supplies, waste
    "monthly_fixed_costs": 18000.0,  # rent, utilities, insurance, salaried labor
}

# F&B businesses famously run ~3-5% net margin; below this there's little room for error.
_SURVIVAL_MARGIN_PCT = 5.0


class ScenarioLabService:
    @classmethod
    def run(cls, base_inputs: dict | None, overrides: dict | None) -> dict[str, Any]:
        inputs = {**DEFAULTS, **{k: v for k, v in (base_inputs or {}).items() if v is not None}}
        ov = overrides or {}
        base = cls._model(inputs, {})
        scenario = cls._model(inputs, ov)
        return {
            "inputs": inputs,
            "overrides": ov,
            "base": base,
            "scenario": scenario,
            "deltas": cls._deltas(base, scenario),
            "insights": cls._insights(base, scenario),
        }

    # ---- pure model (unit-tested) -----------------------------------------

    @staticmethod
    def _model(inputs: dict, ov: dict) -> dict[str, Any]:
        avg_check = inputs["avg_check"] * (1 + ov.get("price_change_pct", 0.0))
        covers = inputs["daily_covers"] * (1 + ov.get("covers_change_pct", 0.0))
        days = inputs["days_open_per_month"]
        var_pct = (
            inputs["food_cost_pct"]
            + ov.get("food_cost_pct_delta", 0.0)
            + inputs["labor_pct"]
            + ov.get("labor_pct_delta", 0.0)
            + inputs["other_variable_pct"]
        )
        var_pct = max(0.0, min(var_pct, 0.99))

        monthly_revenue = avg_check * covers * days
        variable_cost = monthly_revenue * var_pct
        fixed = inputs["monthly_fixed_costs"] + ov.get("monthly_fixed_delta", 0.0)
        monthly_profit = monthly_revenue - variable_cost - fixed
        margin = monthly_profit / monthly_revenue if monthly_revenue else 0.0

        contrib_per_cover = avg_check * (1 - var_pct)
        be_covers = fixed / (contrib_per_cover * days) if contrib_per_cover > 0 and days else None
        return {
            "monthly_revenue": round(monthly_revenue, 2),
            "monthly_profit": round(monthly_profit, 2),
            "profit_margin_pct": round(margin * 100, 1),
            "annual_revenue": round(monthly_revenue * 12, 2),
            "annual_profit": round(monthly_profit * 12, 2),
            "variable_cost_pct": round(var_pct * 100, 1),
            "break_even_covers_per_day": round(be_covers, 1) if be_covers is not None else None,
        }

    @staticmethod
    def _deltas(base: dict, scenario: dict) -> dict[str, Any]:
        keys = (
            "monthly_revenue",
            "monthly_profit",
            "annual_profit",
            "profit_margin_pct",
            "break_even_covers_per_day",
        )
        out: dict[str, Any] = {}
        for k in keys:
            b, s = base.get(k), scenario.get(k)
            out[k] = round(s - b, 2) if b is not None and s is not None else None
        return out

    @staticmethod
    def _insights(base: dict, scenario: dict) -> list[str]:
        out: list[str] = []
        dp = scenario["monthly_profit"] - base["monthly_profit"]
        if abs(dp) >= 1:
            direction = "increase" if dp > 0 else "decrease"
            out.append(
                f"Monthly profit would {direction} by ${abs(round(dp)):,} "
                f"(to ${round(scenario['monthly_profit']):,}/mo)."
            )
        if scenario["monthly_profit"] < 0 <= base["monthly_profit"]:
            out.append(
                "⚠️ This turns a profit into a loss — offset it with volume or pricing before committing."
            )
        elif scenario["monthly_profit"] >= 0 > base["monthly_profit"]:
            out.append("✅ This moves you from a loss back into the black.")
        if 0 <= scenario["profit_margin_pct"] < _SURVIVAL_MARGIN_PCT:
            out.append(
                f"Net margin falls to {scenario['profit_margin_pct']}% — below the ~5% F&B survival line."
            )
        return out
