"""Subscription plans + entitlement logic for PHOW's SaaS tiers.

Pure, dependency-free single source of truth for what each plan can do. `EntitlementService`
resolves a business's plan and applies these limits; routes gate features/quota against them.
"""

from typing import Any

UNLIMITED = -1  # sentinel: no cap
DEFAULT_PLAN = "free"

PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "label": "Starter",
        "price_monthly": 0,
        "limits": {
            "locations": 1,
            "tracked_competitors": 3,
            "feasibility_studies_monthly": 1,
            "scenario_runs_monthly": 3,
            "radar_frequency": "weekly",  # fastest allowed cadence
        },
        "features": {
            "daily_brief": False,  # weekly brief only on free
            "cost_radar": False,
            "review_autopilot": False,
            "email_digest": False,
            "pdf_export": False,
        },
    },
    "pro": {
        "label": "Pro",
        "price_monthly": 59,
        "limits": {
            "locations": 1,
            "tracked_competitors": 15,
            "feasibility_studies_monthly": UNLIMITED,
            "scenario_runs_monthly": UNLIMITED,
            "radar_frequency": "daily",
        },
        "features": {
            "daily_brief": True,
            "cost_radar": True,
            "review_autopilot": True,
            "email_digest": True,
            "pdf_export": True,
        },
    },
    "multi": {
        "label": "Multi-Unit",
        "price_monthly": 149,
        "limits": {
            "locations": 10,
            "tracked_competitors": 50,
            "feasibility_studies_monthly": UNLIMITED,
            "scenario_runs_monthly": UNLIMITED,
            "radar_frequency": "daily",
        },
        "features": {
            "daily_brief": True,
            "cost_radar": True,
            "review_autopilot": True,
            "email_digest": True,
            "pdf_export": True,
        },
    },
}


def plan_name(name: str | None) -> str:
    """Normalize to a known plan id, defaulting to free."""
    key = (name or "").lower()
    return key if key in PLANS else DEFAULT_PLAN


def get_plan(name: str | None) -> dict[str, Any]:
    return PLANS[plan_name(name)]


def limit(name: str | None, key: str) -> Any:
    return get_plan(name)["limits"].get(key)


def has_feature(name: str | None, feature: str) -> bool:
    return bool(get_plan(name)["features"].get(feature, False))


def within_limit(name: str | None, key: str, used: int) -> bool:
    cap = limit(name, key)
    if cap is None or cap == UNLIMITED:
        return True
    return used < cap


def remaining(name: str | None, key: str, used: int) -> int:
    cap = limit(name, key)
    if cap is None or cap == UNLIMITED:
        return UNLIMITED
    return max(0, cap - used)


def entitlements(name: str | None) -> dict[str, Any]:
    plan = get_plan(name)
    return {
        "plan": plan_name(name),
        "label": plan["label"],
        "price_monthly": plan["price_monthly"],
        "limits": plan["limits"],
        "features": plan["features"],
    }


def public_plans() -> list[dict[str, Any]]:
    """Pricing-page view of all plans."""
    return [
        {"id": pid, **{k: p[k] for k in ("label", "price_monthly", "limits", "features")}}
        for pid, p in PLANS.items()
    ]
