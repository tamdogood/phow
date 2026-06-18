"""Request models for the Scenario Lab (what-if margin/break-even calculator)."""

from pydantic import BaseModel, Field


class ScenarioInputs(BaseModel):
    """Baseline unit economics. Any omitted field falls back to an F&B default."""

    avg_check: float | None = None
    daily_covers: float | None = None
    days_open_per_month: float | None = None
    food_cost_pct: float | None = None
    labor_pct: float | None = None
    other_variable_pct: float | None = None
    monthly_fixed_costs: float | None = None


class ScenarioOverrides(BaseModel):
    """The what-if levers (deltas applied to the baseline)."""

    price_change_pct: float = 0.0  # e.g. 0.05 = raise prices 5%
    covers_change_pct: float = 0.0
    food_cost_pct_delta: float = 0.0  # e.g. 0.10 = food cost +10 pts
    labor_pct_delta: float = 0.0
    monthly_fixed_delta: float = 0.0  # e.g. 2000 = rent +$2k/mo


class ScenarioRunRequest(BaseModel):
    business_type: str | None = None
    base: ScenarioInputs | None = None
    overrides: ScenarioOverrides = Field(default_factory=ScenarioOverrides)
