"""Widget data extractor for frontend visualization components.

This module extracts structured data from agent responses that can be
rendered as interactive widgets in the frontend.
"""

import json
import re
from typing import Any


# Registry of widget types and their extractors
WIDGET_REGISTRY = {}


def register_widget(widget_type: str):
    """Decorator to register a widget extractor function."""
    def decorator(func):
        WIDGET_REGISTRY[widget_type] = func
        return func
    return decorator


class WidgetExtractor:
    """Extracts widget data from agent response content."""

    # Pattern to match widget data comments: <!--WIDGET_TYPE:{json_data}-->
    WIDGET_PATTERN = re.compile(r"<!--(\w+_DATA):(\{.*?\})-->", re.DOTALL)

    @classmethod
    def extract_widgets(cls, content: str) -> list[dict[str, Any]]:
        """
        Extract all widget data from content.

        Args:
            content: Agent response content with embedded widget data

        Returns:
            List of widget data dictionaries
        """
        widgets = []

        for match in cls.WIDGET_PATTERN.finditer(content):
            widget_type = match.group(1)
            json_str = match.group(2)

            try:
                data = json.loads(json_str)
                widgets.append({
                    "type": widget_type,
                    "data": data,
                })
            except json.JSONDecodeError:
                continue

        return widgets

    @classmethod
    def inject_widget(cls, widget_type: str, data: dict) -> str:
        """
        Create widget marker string for injection into agent response.

        Args:
            widget_type: Type of widget (e.g., "MARKET_SIZE_DATA")
            data: Widget data dictionary

        Returns:
            Formatted widget marker string
        """
        json_str = json.dumps(data, separators=(",", ":"))
        return f"<!--{widget_type}:{json_str}-->"

    @classmethod
    def strip_widgets(cls, content: str) -> str:
        """Remove widget markers from content for clean display."""
        return cls.WIDGET_PATTERN.sub("", content)


# Widget data formatters


@register_widget("MARKET_SIZE_DATA")
def format_market_size_widget(market_data: dict) -> dict:
    """
    Format market size data for TAM/SAM/SOM visualization widget.

    Expected input: Output from calculate_market_size()
    """
    return {
        "widget_type": "market_size",
        "tam": {
            "value": market_data.get("tam", {}).get("value", 0),
            "label": "Total Addressable Market",
            "formatted": market_data.get("tam", {}).get("formatted", "$0"),
        },
        "sam": {
            "value": market_data.get("sam", {}).get("value", 0),
            "label": "Serviceable Available Market",
            "formatted": market_data.get("sam", {}).get("formatted", "$0"),
        },
        "som": {
            "value": market_data.get("som", {}).get("value", 0),
            "label": "Serviceable Obtainable Market",
            "formatted": market_data.get("som", {}).get("formatted", "$0"),
        },
        "methodology": market_data.get("methodology", {}),
        "confidence": market_data.get("confidence", {}).get("level", "medium"),
    }


@register_widget("INDUSTRY_DATA")
def format_industry_profile_widget(profile_data: dict) -> dict:
    """
    Format industry profile data for visualization widget.

    Expected input: Output from get_industry_profile()
    """
    return {
        "widget_type": "industry_profile",
        "industry_name": profile_data.get("industry_name", "Unknown"),
        "naics_code": profile_data.get("naics_code", ""),
        "employment": {
            "current": profile_data.get("employment", {}).get("current"),
            "growth_rate": profile_data.get("employment", {}).get("growth_rate"),
            "trend": profile_data.get("employment", {}).get("trend"),
        },
        "hierarchy": profile_data.get("hierarchy", []),
    }


@register_widget("LABOR_MARKET_DATA")
def format_labor_market_widget(labor_data: dict) -> dict:
    """
    Format labor market data for visualization widget.

    Expected input: Output from analyze_labor_market()
    """
    return {
        "widget_type": "labor_market",
        "workforce": labor_data.get("workforce", {}),
        "wages": {
            "hourly": labor_data.get("wages", {}).get("hourly_mean"),
            "annual": labor_data.get("wages", {}).get("annual_mean"),
        },
        "hiring_difficulty": {
            "score": labor_data.get("hiring_difficulty", {}).get("score", 50),
            "level": labor_data.get("hiring_difficulty", {}).get("level", "moderate"),
        },
        "recommendations": labor_data.get("recommendations", []),
    }


@register_widget("GROWTH_PROJECTION_DATA")
def format_growth_projection_widget(projection_data: dict) -> dict:
    """
    Format growth projection data for chart visualization.

    Expected input: Output from project_market_growth() or project_market_size()
    """
    projections = projection_data.get("projections", [])

    return {
        "widget_type": "growth_chart",
        "base_value": projection_data.get("base_tam") or projection_data.get("current_market_size", 0),
        "growth_rate": projection_data.get("growth_rate_percent", 0),
        "chart_data": [
            {
                "year": f"Year {p['year']}",
                "value": p["projected_tam"],
            }
            for p in projections
        ],
        "total_growth": projection_data.get("total_growth", "0%"),
    }


def create_market_size_widget(market_data: dict) -> str:
    """Helper to create market size widget from service output."""
    widget_data = format_market_size_widget(market_data)
    return WidgetExtractor.inject_widget("MARKET_SIZE_DATA", widget_data)


def create_industry_widget(profile_data: dict) -> str:
    """Helper to create industry profile widget from service output."""
    widget_data = format_industry_profile_widget(profile_data)
    return WidgetExtractor.inject_widget("INDUSTRY_DATA", widget_data)


def create_labor_market_widget(labor_data: dict) -> str:
    """Helper to create labor market widget from service output."""
    widget_data = format_labor_market_widget(labor_data)
    return WidgetExtractor.inject_widget("LABOR_MARKET_DATA", widget_data)


def create_growth_projection_widget(projection_data: dict) -> str:
    """Helper to create growth projection widget from service output."""
    widget_data = format_growth_projection_widget(projection_data)
    return WidgetExtractor.inject_widget("GROWTH_PROJECTION_DATA", widget_data)


# Economic Intelligence Widgets


@register_widget("ECONOMIC_DATA")
def format_economic_snapshot_widget(economic_data: dict) -> dict:
    """
    Format economic snapshot data for visualization widget.

    Expected input: Output from get_economic_snapshot()
    """
    indicators = economic_data.get("indicators", {})
    outlook = economic_data.get("outlook", {})

    return {
        "widget_type": "economic_snapshot",
        "scope": economic_data.get("scope", "national"),
        "indicators": [
            {
                "name": name.replace("_", " ").title(),
                "value": data.get("value"),
                "units": data.get("units"),
            }
            for name, data in indicators.items()
            if isinstance(data, dict) and "value" in data
        ],
        "outlook": {
            "score": outlook.get("score", 50),
            "level": outlook.get("level", "neutral"),
            "summary": outlook.get("summary", ""),
        },
        "signals": outlook.get("signals", []),
    }


@register_widget("TREND_DATA")
def format_industry_trend_widget(trend_data: dict) -> dict:
    """
    Format industry trend data for visualization widget.

    Expected input: Output from analyze_industry_trends()
    """
    return {
        "widget_type": "industry_trend",
        "industry_name": trend_data.get("industry_name", ""),
        "naics_code": trend_data.get("naics_code", ""),
        "trend_direction": trend_data.get("trend_direction", "stable"),
        "growth_rate": trend_data.get("employment_growth_rate", 0),
        "confidence": trend_data.get("confidence", 0.7),
        "signals": trend_data.get("signals", []),
        "recommendation": trend_data.get("recommendation", ""),
    }


@register_widget("SEASONALITY_DATA")
def format_seasonality_widget(seasonality_data: dict) -> dict:
    """
    Format seasonality data for chart visualization.

    Expected input: Output from get_seasonality_pattern()
    """
    monthly_indices = seasonality_data.get("monthly_indices", {})

    return {
        "widget_type": "seasonality_chart",
        "chart_data": [
            {"month": month, "index": index}
            for month, index in monthly_indices.items()
        ],
        "peak_month": seasonality_data.get("peak_month"),
        "low_month": seasonality_data.get("low_month"),
        "variability": seasonality_data.get("variability", 0),
        "recommendations": seasonality_data.get("recommendations", []),
    }


@register_widget("TIMING_DATA")
def format_entry_timing_widget(timing_data: dict) -> dict:
    """
    Format entry timing data for visualization widget.

    Expected input: Output from analyze_entry_timing()
    """
    return {
        "widget_type": "entry_timing",
        "timing_score": timing_data.get("timing_score", 50),
        "optimal_months": timing_data.get("optimal_months", []),
        "avoid_months": timing_data.get("avoid_months", []),
        "economic_context": timing_data.get("economic_context", {}),
        "industry_context": timing_data.get("industry_context", {}),
        "recommendation": timing_data.get("recommendation", ""),
        "rationale": timing_data.get("rationale", []),
    }


def create_economic_snapshot_widget(economic_data: dict) -> str:
    """Helper to create economic snapshot widget from service output."""
    widget_data = format_economic_snapshot_widget(economic_data)
    return WidgetExtractor.inject_widget("ECONOMIC_DATA", widget_data)


def create_industry_trend_widget(trend_data: dict) -> str:
    """Helper to create industry trend widget from service output."""
    widget_data = format_industry_trend_widget(trend_data)
    return WidgetExtractor.inject_widget("TREND_DATA", widget_data)


def create_seasonality_widget(seasonality_data: dict) -> str:
    """Helper to create seasonality widget from service output."""
    widget_data = format_seasonality_widget(seasonality_data)
    return WidgetExtractor.inject_widget("SEASONALITY_DATA", widget_data)


def create_entry_timing_widget(timing_data: dict) -> str:
    """Helper to create entry timing widget from service output."""
    widget_data = format_entry_timing_widget(timing_data)
    return WidgetExtractor.inject_widget("TIMING_DATA", widget_data)


# Competitive Intelligence Widgets


@register_widget("SWOT_DATA")
def format_swot_widget(swot_data: dict) -> dict:
    """
    Format SWOT analysis data for visualization widget.

    Expected input: Output from generate_swot()
    """
    return {
        "widget_type": "swot_analysis",
        "location": swot_data.get("location", ""),
        "business_type": swot_data.get("business_type", ""),
        "strengths": [
            {"factor": s.get("factor"), "impact": s.get("impact")}
            for s in swot_data.get("strengths", [])
        ],
        "weaknesses": [
            {"factor": w.get("factor"), "impact": w.get("impact")}
            for w in swot_data.get("weaknesses", [])
        ],
        "opportunities": [
            {"factor": o.get("factor"), "impact": o.get("impact")}
            for o in swot_data.get("opportunities", [])
        ],
        "threats": [
            {"factor": t.get("factor"), "impact": t.get("impact")}
            for t in swot_data.get("threats", [])
        ],
        "assessment": swot_data.get("assessment", {}),
    }


@register_widget("FIVE_FORCES_DATA")
def format_five_forces_widget(forces_data: dict) -> dict:
    """
    Format Porter's Five Forces data for visualization widget.

    Expected input: Output from analyze_five_forces()
    """
    forces = forces_data.get("forces", {})
    return {
        "widget_type": "five_forces",
        "location": forces_data.get("location", ""),
        "business_type": forces_data.get("business_type", ""),
        "forces": [
            {
                "name": "Competitive Rivalry",
                "score": forces.get("competitive_rivalry", {}).get("score", 50),
                "level": forces.get("competitive_rivalry", {}).get("level", "medium"),
            },
            {
                "name": "Supplier Power",
                "score": forces.get("supplier_power", {}).get("score", 50),
                "level": forces.get("supplier_power", {}).get("level", "medium"),
            },
            {
                "name": "Buyer Power",
                "score": forces.get("buyer_power", {}).get("score", 50),
                "level": forces.get("buyer_power", {}).get("level", "medium"),
            },
            {
                "name": "Threat of Substitutes",
                "score": forces.get("threat_of_substitutes", {}).get("score", 50),
                "level": forces.get("threat_of_substitutes", {}).get("level", "medium"),
            },
            {
                "name": "Threat of New Entrants",
                "score": forces.get("threat_of_new_entrants", {}).get("score", 50),
                "level": forces.get("threat_of_new_entrants", {}).get("level", "medium"),
            },
        ],
        "overall": forces_data.get("overall", {}),
    }


@register_widget("PRICING_DATA")
def format_pricing_widget(pricing_data: dict) -> dict:
    """
    Format pricing landscape data for visualization widget.

    Expected input: Output from analyze_pricing_landscape()
    """
    distribution = pricing_data.get("distribution", {})
    return {
        "widget_type": "pricing_landscape",
        "location": pricing_data.get("location", ""),
        "business_type": pricing_data.get("business_type", ""),
        "chart_data": [
            {"tier": "$", "count": distribution.get("$", 0)},
            {"tier": "$$", "count": distribution.get("$$", 0)},
            {"tier": "$$$", "count": distribution.get("$$$", 0)},
            {"tier": "$$$$", "count": distribution.get("$$$$", 0)},
        ],
        "dominant_tier": pricing_data.get("dominant_tier", "$$"),
        "pricing_gaps": pricing_data.get("pricing_gaps", []),
        "recommendation": pricing_data.get("recommendation", ""),
    }


@register_widget("MARKET_SHARE_DATA")
def format_market_share_widget(share_data: dict) -> dict:
    """
    Format market share data for visualization widget.

    Expected input: Output from estimate_market_shares()
    """
    return {
        "widget_type": "market_share",
        "location": share_data.get("location", ""),
        "business_type": share_data.get("business_type", ""),
        "chart_data": [
            {"name": s.get("name"), "share": s.get("share_percent")}
            for s in share_data.get("shares", [])[:10]
        ],
        "market_leader": share_data.get("market_leader", {}),
        "concentration": share_data.get("concentration", {}),
    }


def create_swot_widget(swot_data: dict) -> str:
    """Helper to create SWOT widget from service output."""
    widget_data = format_swot_widget(swot_data)
    return WidgetExtractor.inject_widget("SWOT_DATA", widget_data)


def create_five_forces_widget(forces_data: dict) -> str:
    """Helper to create Five Forces widget from service output."""
    widget_data = format_five_forces_widget(forces_data)
    return WidgetExtractor.inject_widget("FIVE_FORCES_DATA", widget_data)


def create_pricing_widget(pricing_data: dict) -> str:
    """Helper to create pricing landscape widget from service output."""
    widget_data = format_pricing_widget(pricing_data)
    return WidgetExtractor.inject_widget("PRICING_DATA", widget_data)


def create_market_share_widget(share_data: dict) -> str:
    """Helper to create market share widget from service output."""
    widget_data = format_market_share_widget(share_data)
    return WidgetExtractor.inject_widget("MARKET_SHARE_DATA", widget_data)


# Consumer Insights Widgets


@register_widget("SENTIMENT_DATA")
def format_sentiment_widget(sentiment_data: dict) -> dict:
    """
    Format sentiment analysis data for visualization widget.

    Expected input: Output from analyze_sentiment()
    """
    aspects = sentiment_data.get("aspect_sentiments", {})
    return {
        "widget_type": "sentiment_analysis",
        "location": sentiment_data.get("location", ""),
        "business_type": sentiment_data.get("business_type", ""),
        "overall_sentiment": sentiment_data.get("overall_sentiment", 0),
        "sentiment_label": sentiment_data.get("sentiment_label", "neutral"),
        "average_rating": sentiment_data.get("average_rating"),
        "aspect_chart": [
            {"aspect": aspect.replace("_", " ").title(), "sentiment": data.get("sentiment", 0)}
            for aspect, data in aspects.items()
        ],
        "review_count": sentiment_data.get("review_count", 0),
        "confidence": sentiment_data.get("confidence", 0),
    }


@register_widget("PAIN_POINTS_DATA")
def format_pain_points_widget(pain_data: dict) -> dict:
    """
    Format pain points data for visualization widget.

    Expected input: Output from identify_pain_points()
    """
    return {
        "widget_type": "pain_points",
        "location": pain_data.get("location", ""),
        "business_type": pain_data.get("business_type", ""),
        "pain_points": [
            {
                "issue": pp.get("issue"),
                "frequency": pp.get("frequency"),
                "severity": pp.get("severity"),
            }
            for pp in pain_data.get("pain_points", [])[:8]
        ],
        "opportunities": [
            {
                "opportunity": opp.get("opportunity"),
                "priority": opp.get("priority"),
            }
            for opp in pain_data.get("opportunities", [])[:5]
        ],
    }


@register_widget("CUSTOMER_JOURNEY_DATA")
def format_journey_widget(journey_data: dict) -> dict:
    """
    Format customer journey data for visualization widget.

    Expected input: Output from map_customer_journey()
    """
    return {
        "widget_type": "customer_journey",
        "business_type": journey_data.get("business_type", ""),
        "stages": [
            {
                "name": stage.get("stage"),
                "description": stage.get("description"),
                "touchpoints": stage.get("touchpoints", [])[:4],
            }
            for stage in journey_data.get("journey_stages", [])
        ],
        "key_moments": journey_data.get("key_moments", []),
    }


@register_widget("CONSUMER_PROFILE_DATA")
def format_profile_widget(profile_data: dict) -> dict:
    """
    Format consumer profile data for visualization widget.

    Expected input: Output from build_consumer_profile()
    """
    persona = profile_data.get("primary_persona", {})
    return {
        "widget_type": "consumer_profile",
        "location": profile_data.get("location", ""),
        "business_type": profile_data.get("business_type", ""),
        "persona": {
            "name": persona.get("name"),
            "income_segment": persona.get("income_segment"),
            "age_group": persona.get("age_group"),
            "values": persona.get("values", [])[:4],
            "price_sensitivity": persona.get("price_sensitivity"),
            "channels": persona.get("channels", [])[:3],
        },
        "targeting": [
            {
                "area": rec.get("area"),
                "recommendation": rec.get("recommendation"),
            }
            for rec in profile_data.get("targeting_recommendations", [])[:3]
        ],
    }


def create_sentiment_widget(sentiment_data: dict) -> str:
    """Helper to create sentiment widget from service output."""
    widget_data = format_sentiment_widget(sentiment_data)
    return WidgetExtractor.inject_widget("SENTIMENT_DATA", widget_data)


def create_pain_points_widget(pain_data: dict) -> str:
    """Helper to create pain points widget from service output."""
    widget_data = format_pain_points_widget(pain_data)
    return WidgetExtractor.inject_widget("PAIN_POINTS_DATA", widget_data)


def create_journey_widget(journey_data: dict) -> str:
    """Helper to create customer journey widget from service output."""
    widget_data = format_journey_widget(journey_data)
    return WidgetExtractor.inject_widget("CUSTOMER_JOURNEY_DATA", widget_data)


def create_profile_widget(profile_data: dict) -> str:
    """Helper to create consumer profile widget from service output."""
    widget_data = format_profile_widget(profile_data)
    return WidgetExtractor.inject_widget("CONSUMER_PROFILE_DATA", widget_data)


# Financial Projection Widgets


@register_widget("FINANCIAL_PROJECTION_DATA")
def format_financial_projection_widget(projection_data: dict) -> dict:
    """
    Format revenue projection data for visualization widget.

    Expected input: Output from project_revenue() or get_financial_summary()
    """
    scenarios = projection_data.get("revenue_scenarios", {})
    if not scenarios:
        # Single scenario projection
        scenarios = {
            projection_data.get("scenario", "moderate"): projection_data.get("projections", {})
        }

    return {
        "widget_type": "revenue_projection",
        "location": projection_data.get("location", ""),
        "business_type": projection_data.get("business_type", ""),
        "chart_data": [
            {
                "scenario": "Conservative",
                "annual": scenarios.get("conservative", {}).get("annual_revenue", 0),
                "monthly": scenarios.get("conservative", {}).get("monthly_revenue", 0),
            },
            {
                "scenario": "Moderate",
                "annual": scenarios.get("moderate", {}).get("annual_revenue", 0),
                "monthly": scenarios.get("moderate", {}).get("monthly_revenue", 0),
            },
            {
                "scenario": "Optimistic",
                "annual": scenarios.get("optimistic", {}).get("annual_revenue", 0),
                "monthly": scenarios.get("optimistic", {}).get("monthly_revenue", 0),
            },
        ],
        "benchmark": projection_data.get("benchmark_comparison", {}),
    }


@register_widget("BREAK_EVEN_DATA")
def format_break_even_widget(break_even_data: dict) -> dict:
    """
    Format break-even analysis data for visualization widget.

    Expected input: Output from calculate_break_even()
    """
    return {
        "widget_type": "break_even",
        "location": break_even_data.get("location", ""),
        "business_type": break_even_data.get("business_type", ""),
        "break_even_revenue": break_even_data.get("break_even_revenue", {}),
        "break_even_units": break_even_data.get("break_even_units", {}),
        "startup_recovery": {
            "startup_costs": break_even_data.get("startup_recovery", {}).get("startup_costs"),
            "months_to_recover": break_even_data.get("startup_recovery", {}).get("months_to_recover"),
        },
        "benchmark": break_even_data.get("benchmark_comparison", {}),
    }


@register_widget("SCENARIO_COMPARISON_DATA")
def format_scenario_widget(scenario_data: dict) -> dict:
    """
    Format scenario comparison data for visualization widget.

    Expected input: Output from run_scenario()
    """
    return {
        "widget_type": "scenario_comparison",
        "scenario_name": scenario_data.get("scenario_name", "Custom Scenario"),
        "base_case": scenario_data.get("base_case", {}),
        "scenario_case": scenario_data.get("scenario_case", {}),
        "impact": scenario_data.get("impact", {}),
        "modifications": scenario_data.get("modifications_applied", {}),
    }


@register_widget("VIABILITY_DATA")
def format_viability_widget(viability_data: dict) -> dict:
    """
    Format financial viability data for visualization widget.

    Expected input: Output from calculate_financial_viability()
    """
    return {
        "widget_type": "financial_viability",
        "location": viability_data.get("location", ""),
        "business_type": viability_data.get("business_type", ""),
        "viability_score": viability_data.get("viability_score", 0),
        "viability_level": viability_data.get("viability_level", "moderate"),
        "score_breakdown": [
            {"factor": k.replace("_", " ").title(), "score": v}
            for k, v in viability_data.get("score_breakdown", {}).items()
        ],
        "recommendation": viability_data.get("recommendation", ""),
        "risk_factors": viability_data.get("risk_factors", []),
    }


def create_financial_projection_widget(projection_data: dict) -> str:
    """Helper to create financial projection widget from service output."""
    widget_data = format_financial_projection_widget(projection_data)
    return WidgetExtractor.inject_widget("FINANCIAL_PROJECTION_DATA", widget_data)


def create_break_even_widget(break_even_data: dict) -> str:
    """Helper to create break-even widget from service output."""
    widget_data = format_break_even_widget(break_even_data)
    return WidgetExtractor.inject_widget("BREAK_EVEN_DATA", widget_data)


def create_scenario_widget(scenario_data: dict) -> str:
    """Helper to create scenario comparison widget from service output."""
    widget_data = format_scenario_widget(scenario_data)
    return WidgetExtractor.inject_widget("SCENARIO_COMPARISON_DATA", widget_data)


def create_viability_widget(viability_data: dict) -> str:
    """Helper to create viability widget from service output."""
    widget_data = format_viability_widget(viability_data)
    return WidgetExtractor.inject_widget("VIABILITY_DATA", widget_data)


# Report & Recommendations Widgets


@register_widget("EXECUTIVE_SUMMARY_DATA")
def format_executive_summary_widget(summary_data: dict) -> dict:
    """
    Format executive summary data for visualization widget.

    Expected input: Output from get_executive_summary()
    """
    recommendation = summary_data.get("recommendation", {})
    return {
        "widget_type": "executive_summary",
        "location": summary_data.get("location") or summary_data.get("metadata", {}).get("location", ""),
        "business_type": summary_data.get("business_type") or summary_data.get("metadata", {}).get("business_type", ""),
        "summary_paragraphs": summary_data.get("summary_paragraphs", []),
        "key_findings": summary_data.get("key_findings", []),
        "recommendation": {
            "verdict": recommendation.get("verdict", "neutral"),
            "rationale": recommendation.get("rationale", ""),
        },
    }


@register_widget("RECOMMENDATIONS_DATA")
def format_recommendations_widget(recommendations_data: dict) -> dict:
    """
    Format recommendations data for visualization widget.

    Expected input: Output from get_key_recommendations()
    """
    recommendations = recommendations_data.get("recommendations", [])
    return {
        "widget_type": "recommendations",
        "location": recommendations_data.get("location", ""),
        "business_type": recommendations_data.get("business_type", ""),
        "total_count": len(recommendations),
        "recommendations": [
            {
                "title": r.get("title"),
                "description": r.get("description"),
                "priority": r.get("priority", "medium"),
                "category": r.get("category", "strategic_considerations"),
            }
            for r in recommendations[:8]
        ],
        "by_priority": {
            "high": len([r for r in recommendations if r.get("priority") == "high"]),
            "medium": len([r for r in recommendations if r.get("priority") == "medium"]),
            "low": len([r for r in recommendations if r.get("priority") == "low"]),
        },
    }


def create_executive_summary_widget(summary_data: dict) -> str:
    """Helper to create executive summary widget from service output."""
    widget_data = format_executive_summary_widget(summary_data)
    return WidgetExtractor.inject_widget("EXECUTIVE_SUMMARY_DATA", widget_data)


def create_recommendations_widget(recommendations_data: dict) -> str:
    """Helper to create recommendations widget from service output."""
    widget_data = format_recommendations_widget(recommendations_data)
    return WidgetExtractor.inject_widget("RECOMMENDATIONS_DATA", widget_data)
