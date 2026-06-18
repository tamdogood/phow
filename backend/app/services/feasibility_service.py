"""Feasibility Study orchestration.

Runs a DETERMINISTIC pipeline that always produces a complete food & drink
feasibility report by calling the existing analysis services in a fixed order,
then reuses ``report_service`` for synthesis (executive summary + verdict +
recommendations). Every leg is best-effort: a failure degrades that section to
"unavailable" rather than aborting the report.
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from ..core.logging import get_logger
from ..repositories.feasibility_repository import FeasibilityRepository
from ..services.report_service import get_report_service
from ..services.market_analysis_service import get_market_analysis_service
from ..services.competitive_analysis_service import get_competitive_analysis_service
from ..services.consumer_analysis_service import get_consumer_analysis_service
from ..services.economic_service import get_economic_service
from ..services.financial_analysis_service import get_financial_analysis_service
from ..tools.market_validator.agent_tools import (
    get_location_demographics,
    calculate_market_viability,
)
from ..tools.competitor_analyzer.agent_tools import find_competitors, create_positioning_map
from ..tools.location_scout.google_maps import GoogleMapsClient
from ..tools.market_research.widget_extractor import (
    format_market_size_widget,
    format_swot_widget,
    format_five_forces_widget,
    format_pricing_widget,
    format_market_share_widget,
    format_sentiment_widget,
    format_pain_points_widget,
    format_profile_widget,
    format_financial_projection_widget,
    format_break_even_widget,
    format_viability_widget,
    format_economic_snapshot_widget,
    format_seasonality_widget,
    format_entry_timing_widget,
)

logger = get_logger("feasibility_service")

_STATE_RE = re.compile(r",\s*([A-Z]{2})\s+\d{5}")
_STEPS_TOTAL = 7
_DEFAULT_NAICS = "722511"  # Full-service restaurants


class FeasibilityService:
    """Deterministic feasibility-study orchestrator."""

    def __init__(self, db: Client):
        self.db = db
        self.repo = FeasibilityRepository(db)
        self.maps = GoogleMapsClient()
        self.market = get_market_analysis_service()
        self.competitive = get_competitive_analysis_service()
        self.consumer = get_consumer_analysis_service()
        self.economic = get_economic_service()
        self.financial = get_financial_analysis_service()
        self.report = get_report_service()

    # ---- CRUD / lifecycle -------------------------------------------------

    async def create_report(
        self,
        *,
        session_id: str,
        concept: str,
        location_address: str,
        user_id: str | None = None,
        business_profile_id: str | None = None,
        scale_seats: int | None = None,
        startup_budget: int | None = None,
    ) -> dict[str, Any]:
        row = await self.repo.create(
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": user_id,
                "business_profile_id": business_profile_id,
                "concept": concept,
                "location_address": location_address,
                "scale_seats": scale_seats,
                "startup_budget": startup_budget,
                "status": "pending",
                "progress": {"step": 0, "steps_total": _STEPS_TOTAL, "label": "Queued"},
            }
        )
        try:
            from ..workers.feasibility_tasks import run_feasibility_report

            run_feasibility_report.delay(row["id"])
        except Exception as e:
            logger.warning(
                "Failed to dispatch feasibility task", report_id=row.get("id"), error=str(e)
            )
        return row

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        return await self.repo.get_by_id(report_id)

    async def list_reports(
        self, session_id: str | None = None, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        if user_id:
            return await self.repo.list_by_user(user_id)
        if session_id:
            return await self.repo.list_by_session(session_id)
        return []

    async def delete_report(self, report_id: str) -> bool:
        return await self.repo.delete(report_id)

    async def rerun(self, report_id: str) -> dict[str, Any]:
        report = await self.repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")
        await self.repo.update(report_id, {"status": "pending", "error": None})
        try:
            from ..workers.feasibility_tasks import run_feasibility_report

            run_feasibility_report.delay(report_id)
        except Exception as e:
            logger.warning("Failed to dispatch feasibility task", report_id=report_id, error=str(e))
        return {"report_id": report_id, "status": "pending"}

    # ---- Pipeline (called by the Celery worker) ---------------------------

    async def run_pipeline(self, report_id: str) -> None:
        row = await self.repo.get_by_id(report_id)
        if not row:
            logger.error("Feasibility report not found", report_id=report_id)
            return
        try:
            await self.repo.update(
                report_id,
                {
                    "status": "running",
                    "progress": {
                        "step": 1,
                        "steps_total": _STEPS_TOTAL,
                        "label": "Locating & demographics",
                    },
                },
            )
            report = await self._build(
                report_id,
                concept=row["concept"],
                address=row["location_address"],
                scale_seats=row.get("scale_seats"),
                startup_budget=row.get("startup_budget"),
            )
            verdict = report["verdict"]
            loc = report["meta"]["location"]
            await self.repo.update(
                report_id,
                {
                    "status": "completed",
                    "report": report,
                    "verdict": verdict["decision"],
                    "viability_score": verdict["score"],
                    "title": report["meta"]["title"],
                    "naics_code": report["meta"]["naics_code"],
                    "location_lat": loc.get("lat"),
                    "location_lng": loc.get("lng"),
                    "progress": {
                        "step": _STEPS_TOTAL,
                        "steps_total": _STEPS_TOTAL,
                        "label": "Complete",
                    },
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            logger.info(
                "Feasibility report completed",
                report_id=report_id,
                verdict=verdict["decision"],
                score=verdict["score"],
            )
        except Exception as e:
            logger.error(
                "Feasibility pipeline failed",
                report_id=report_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            await self.repo.update(report_id, {"status": "failed", "error": str(e)})

    async def _build(
        self,
        report_id: str,
        *,
        concept: str,
        address: str,
        scale_seats: int | None,
        startup_budget: int | None,
    ) -> dict[str, Any]:
        business_type = concept

        # --- Stage A: foundation (location + demographics + glue) ---
        naics_codes = self.market.naics_service.map_business_type(business_type)
        naics = naics_codes[0] if naics_codes else _DEFAULT_NAICS

        demo_res = await self._safe(
            get_location_demographics.ainvoke({"address": address}), {}, "demographics"
        )
        location = demo_res.get("location") if isinstance(demo_res, dict) else None
        if not location or "lat" not in location:
            raise RuntimeError(f"Could not resolve a location for '{address}'")
        lat, lng = location["lat"], location["lng"]
        formatted = location.get("formatted_address", address)
        nested_demo = demo_res.get("demographics", {}) or {}
        geography = demo_res.get("geography", {}) or {}
        state = self._parse_state(formatted)
        city = self._parse_city(formatted, geography)
        flat_demo = self._flatten_demographics(nested_demo)

        await self._progress(report_id, 2, "Analyzing competitors & market")

        # --- Stage B: independent legs in parallel ---
        viability, competitors_res, positioning, econ, growth, health, walk, trends = (
            await asyncio.gather(
                self._safe(
                    calculate_market_viability.ainvoke(
                        {"address": address, "business_type": business_type}
                    ),
                    {},
                    "viability",
                ),
                self._safe(
                    find_competitors.ainvoke({"address": address, "business_type": business_type}),
                    {},
                    "competitors",
                ),
                self._safe(
                    create_positioning_map.ainvoke(
                        {"address": address, "business_type": business_type}
                    ),
                    {},
                    "positioning",
                ),
                self._safe(self.economic.get_economic_snapshot(state), {}, "economic"),
                self._safe(self.market.calculate_growth_rate(naics), {}, "growth"),
                self._fnb_health(lat, lng, city),
                self._fnb_walk(lat, lng, formatted),
                self._fnb_trends(concept, city),
            )
        )
        competitors_list = (
            competitors_res.get("competitors", []) if isinstance(competitors_res, dict) else []
        )
        comp_count = (
            competitors_res.get("total_found", len(competitors_list))
            if isinstance(competitors_res, dict)
            else 0
        )

        await self._progress(report_id, 3, "Reading competitor reviews")

        # --- Stage C: consumer reviews (need competitor place_ids) ---
        reviews = await self._fetch_reviews(competitors_list)
        popular = await self._fnb_popular(competitors_list)

        await self._progress(report_id, 4, "Sizing the market")

        # --- Stage D: market sizing (reuse foundation demographics) ---
        market_size = await self._safe(
            self.market.calculate_market_size(
                {"lat": lat, "lng": lng, "demographics": nested_demo},
                business_type,
                5.0,
                comp_count,
            ),
            {},
            "market_size",
        )

        # --- Stage F (part 1): fast sync analytics ---
        seasonality = self._safe_sync(
            self.economic.get_seasonality_pattern, naics, default={}, label="seasonality"
        )
        sentiment = self._safe_sync(
            self.consumer.analyze_sentiment, reviews, default={}, label="sentiment"
        )
        pain = self._safe_sync(
            self.consumer.identify_pain_points, reviews, default={}, label="pain_points"
        )
        profile = self._safe_sync(
            self.consumer.build_consumer_profile,
            location,
            business_type,
            flat_demo,
            reviews,
            default={},
            label="profile",
        )

        # --- Stage E: the shared FLAT market_data bundle ---
        market_data = self._build_market_data(
            competitors_list,
            flat_demo,
            market_size,
            growth,
            econ,
            seasonality,
            positioning,
            pain,
            viability,
        )

        await self._progress(report_id, 5, "Competitive & financial analysis")

        # --- Stage F (part 2): competitive + financial ---
        swot = await self._safe(
            self.competitive.generate_swot(location, business_type, market_data), {}, "swot"
        )
        five_forces = await self._safe(
            self.competitive.analyze_five_forces(business_type, location, market_data),
            {},
            "five_forces",
        )
        pricing = self._safe_sync(
            self.competitive.analyze_pricing_landscape,
            competitors_list,
            default={},
            label="pricing",
        )
        market_share = self._safe_sync(
            self.competitive.estimate_market_shares,
            competitors_list,
            default={},
            label="market_share",
        )
        financial = self._safe_sync(
            self.financial.get_financial_summary,
            business_type,
            location,
            market_data,
            default={},
            label="financial",
        )

        await self._progress(report_id, 6, "Assessing entry timing")
        entry_timing = await self._safe(
            self.economic.analyze_entry_timing(
                business_type, {"state": state, "lat": lat, "lng": lng}
            ),
            {},
            "entry_timing",
        )

        await self._progress(report_id, 7, "Synthesizing the verdict")

        # --- Stage H: synthesis (reuse report_service) ---
        analysis_results = {
            "location": formatted,
            "business_type": business_type,
            "viability": {
                "score": (financial.get("viability") or {}).get("score"),
                "level": (financial.get("viability") or {}).get("level"),
            },
            "market_size": {
                "tam": market_size.get("tam"),
                "sam": market_size.get("sam"),
                "som": market_size.get("som"),
                "methodology": market_size.get("methodology"),
                "confidence": market_size.get("confidence"),
            },
            "competitors": competitors_res,
            "swot": swot,
            "five_forces": five_forces,
            "pricing": pricing,
            "sentiment": sentiment,
            "pain_points": pain,
            "consumer_profile": profile,
            "financial_summary": financial,
            "economic": {
                "outlook": (econ or {}).get("outlook", {}),
                "indicators": (econ or {}).get("indicators", {}),
            },
        }
        report_data = self.report.aggregate_report_data(analysis_results)
        exec_summary = await self._safe(
            self.report.generate_executive_summary(report_data), {}, "exec_summary"
        )
        recommendations = await self._safe(
            self.report.generate_recommendations(report_data), [], "recommendations"
        )
        verdict = self._build_verdict(financial, viability, swot, exec_summary, market_size)

        # --- Stage I: assemble the report artifact ---
        return {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "title": f"{concept.strip().title()} — {formatted}",
                "concept": concept,
                "business_type": business_type,
                "location": {
                    "address": formatted,
                    "lat": lat,
                    "lng": lng,
                    "place_id": location.get("place_id"),
                },
                "naics_code": naics,
                "scale_seats": scale_seats,
                "startup_budget": startup_budget,
                "schema_version": 1,
            },
            "verdict": verdict,
            "exec_summary": {
                "summary_paragraphs": exec_summary.get("summary_paragraphs", []),
                "key_findings": exec_summary.get("key_findings", []),
                "recommendation": exec_summary.get("recommendation", {}),
            },
            "sections": {
                "location": viability or None,
                "market_size": format_market_size_widget(market_size) if market_size else None,
                "competition": {
                    "competitors": competitors_res or None,
                    "positioning": positioning or None,
                    "swot": format_swot_widget(swot) if swot else None,
                    "five_forces": format_five_forces_widget(five_forces) if five_forces else None,
                    "pricing": format_pricing_widget(pricing) if self._ok(pricing) else None,
                    "market_share": (
                        format_market_share_widget(market_share) if self._ok(market_share) else None
                    ),
                },
                "consumer": {
                    "sentiment": format_sentiment_widget(sentiment) if sentiment else None,
                    "pain_points": format_pain_points_widget(pain) if pain else None,
                    "profile": format_profile_widget(profile) if profile else None,
                    "data_available": bool(reviews),
                    "reviews_analyzed": len(reviews),
                },
                "economic": {
                    "snapshot": format_economic_snapshot_widget(econ) if econ else None,
                    "seasonality": format_seasonality_widget(seasonality) if seasonality else None,
                    "entry_timing": (
                        format_entry_timing_widget(entry_timing) if entry_timing else None
                    ),
                },
                "financial": self._financial_section(financial, business_type, market_data),
                "fnb_signals": {
                    "health_inspections": health,
                    "walkability": walk,
                    "search_trends": trends,
                    "popular_times": popular,
                },
                "recommendations": recommendations,
            },
            "sources": self._build_sources(
                market_size, competitors_res, econ, financial, naics, health, walk, trends
            ),
        }

    # ---- glue / helpers ---------------------------------------------------

    @staticmethod
    def _flatten_demographics(nested: dict) -> dict[str, Any]:
        """Reconcile nested Census shape with the flat shape the analysis services read."""
        return {
            "total_population": (nested.get("population") or {}).get("total"),
            "median_income": (nested.get("income") or {}).get("median_household"),
            "median_age": (nested.get("age_distribution") or {}).get("median_age"),
            "age_distribution": nested.get("age_distribution", {}),
            "education": nested.get("education", {}),
        }

    def _build_market_data(
        self,
        competitors,
        flat_demo,
        market_size,
        growth,
        econ,
        seasonality,
        positioning,
        pain,
        viability,
    ) -> dict[str, Any]:
        return {
            "competitors": competitors,
            "demographics": flat_demo,
            "som": market_size.get("som", {}),
            "trends": {
                "trend_direction": self._trend_direction(growth),
                "employment_growth_rate": (growth or {}).get("blended_growth_rate", 0),
            },
            "economic": {"outlook": (econ or {}).get("outlook", {})},
            "seasonality": {"variability": (seasonality or {}).get("variability", 0)},
            "positioning": {"market_gaps": (positioning or {}).get("market_gaps", [])},
            "pain_points": (pain or {}).get("pain_points", []),
            "foot_traffic": {
                "score": (viability.get("score_breakdown") or {}).get("foot_traffic_score", 0)
            },
        }

    @staticmethod
    def _trend_direction(growth: dict | None) -> str:
        rate = (growth or {}).get("blended_growth_rate", 0) or 0
        if rate > 3:
            return "strongly_growing"
        if rate > 0:
            return "growing"
        if rate < 0:
            return "declining"
        return "stable"

    def _financial_section(
        self, financial: dict, business_type: str, market_data: dict
    ) -> dict | None:
        if not financial:
            return None
        section = dict(financial)
        section["projection_widget"] = format_financial_projection_widget(financial)
        try:
            moderate = {
                "projections": (financial.get("revenue_scenarios") or {}).get("moderate", {})
            }
            fv = self.financial.calculate_financial_viability(business_type, moderate, market_data)
            section["viability_widget"] = format_viability_widget(fv)
            be = self.financial.calculate_break_even(business_type, moderate)
            section["break_even_widget"] = format_break_even_widget(be)
        except Exception as e:
            logger.warning("Financial widget derivation failed", error=str(e))
        return section

    @staticmethod
    def _build_verdict(financial, viability, swot, exec_summary, market_size) -> dict[str, Any]:
        scores: list[float] = []
        fv = (financial.get("viability") or {}).get("score")
        if fv is not None:
            scores.append(fv)
        lv = viability.get("viability_score")
        if lv is not None:
            scores.append(lv)
        sa = (swot.get("assessment") or {}).get("score")
        if sa is not None:
            scores.append(sa)
        score = int(round(sum(scores) / len(scores))) if scores else 50
        if score >= 65:
            decision = "GO"
        elif score >= 45:
            decision = "GO_WITH_CONDITIONS"
        else:
            decision = "NO_GO"
        rationale = (exec_summary.get("recommendation") or {}).get("rationale") or (
            "Synthesis of demographics, competition, demand and financial projections for this location."
        )
        confidence = (market_size.get("confidence") or {}).get("level", "medium")
        return {
            "decision": decision,
            "score": score,
            "rationale": rationale,
            "confidence": confidence,
        }

    def _build_sources(
        self, market_size, competitors_res, econ, financial, naics, health, walk, trends
    ) -> list[dict]:
        sources: list[dict] = []
        if market_size:
            sources.append(
                {
                    "section": "market_size",
                    "label": "U.S. Census ACS 5-Year + BLS spending model",
                    "detail": f"NAICS {naics} · TAM/SAM/SOM model",
                    "confidence": (market_size.get("confidence") or {}).get("level", "medium"),
                }
            )
        if competitors_res:
            s = competitors_res.get("sources", {})
            sources.append(
                {
                    "section": "competition",
                    "label": "Google Places + Yelp Fusion",
                    "detail": f"{competitors_res.get('total_found', 0)} businesses (Google {s.get('google', 0)}, Yelp {s.get('yelp', 0)})",
                    "confidence": "high",
                }
            )
        if econ and econ.get("indicators"):
            sources.append(
                {
                    "section": "economic",
                    "label": "FRED — Federal Reserve Economic Data",
                    "detail": "GDP, unemployment, CPI, consumer confidence",
                    "confidence": "high",
                }
            )
        if financial:
            sources.append(
                {
                    "section": "financial",
                    "label": f"Industry benchmarks (NAICS {naics})",
                    "detail": "Revenue, margins, break-even and startup costs",
                    "confidence": "medium",
                }
            )
        for sig, label, detail, conf in [
            (
                health,
                "City health-department open data",
                "Restaurant inspection landscape",
                "medium",
            ),
            (walk, "Walk Score API", "Walkability, transit & bike scores", "medium"),
            (trends, "Google Trends", "Local search-interest momentum", "low"),
        ]:
            if isinstance(sig, dict) and "status" not in sig:
                sources.append(
                    {
                        "section": "fnb_signals",
                        "label": sig.get("source", label),
                        "detail": detail,
                        "confidence": conf,
                    }
                )
        return sources

    # ---- food & drink signals (best-effort, never block) ------------------

    async def _fnb_health(self, lat: float, lng: float, city: str | None) -> dict[str, Any]:
        if not city:
            return {"status": "unavailable", "reason": "Could not determine city"}
        try:
            from ..clients import get_health_inspection_client

            res = await asyncio.wait_for(
                get_health_inspection_client().get_inspections_nearby(lat, lng, city), timeout=12
            )
            if res and res.get("total_restaurants"):
                res.setdefault("source", f"{city} health department open data")
                return res
        except Exception as e:
            logger.warning("Health inspections unavailable", error=str(e))
        return {"status": "unavailable", "reason": f"No health-inspection open data for {city}"}

    async def _fnb_walk(self, lat: float, lng: float, address: str) -> dict[str, Any]:
        try:
            from ..clients import get_walkscore_client

            res = await asyncio.wait_for(
                get_walkscore_client().get_score(lat, lng, address), timeout=10
            )
            if res and res.get("walkscore") is not None:
                res.setdefault("source", "Walk Score API")
                return res
        except Exception as e:
            logger.warning("Walk Score unavailable", error=str(e))
        return {"status": "unavailable"}

    async def _fnb_trends(self, concept: str, city: str | None) -> dict[str, Any]:
        try:
            from ..clients import get_trends_client

            res = await asyncio.wait_for(
                get_trends_client().get_interest_over_time([concept, f"{concept} near me"], city),
                timeout=10,
            )
            if res and res.get("data"):
                res["momentum"] = self._trend_momentum(res)
                res.setdefault("source", "Google Trends")
                return res
        except Exception as e:
            logger.warning("Search trends unavailable", error=str(e))
        return {"status": "unavailable"}

    async def _fnb_popular(self, competitors: list[dict]) -> dict[str, Any]:
        for c in (competitors or [])[:3]:
            pid = c.get("place_id")
            if not pid:
                continue
            try:
                res = await asyncio.wait_for(self.maps.get_popular_times(pid), timeout=8)
                if res:
                    res.setdefault("source", f"Google Places — {c.get('name')}")
                    return res
            except Exception:
                continue
        return {"status": "unavailable"}

    @staticmethod
    def _trend_momentum(res: dict) -> str:
        try:
            vals: list[float] = []
            for pt in res.get("data") or []:
                if isinstance(pt, dict):
                    for v in pt.values():
                        if isinstance(v, (int, float)):
                            vals.append(v)
                            break
            if len(vals) >= 4:
                third = max(1, len(vals) // 3)
                first = sum(vals[:third]) or 1
                last = sum(vals[-third:])
                if last > first * 1.1:
                    return "rising"
                if last < first * 0.9:
                    return "declining"
            return "flat"
        except Exception:
            return "flat"

    async def _fetch_reviews(self, competitors: list[dict]) -> list[dict]:
        pids = [c["place_id"] for c in (competitors or [])[:5] if c.get("place_id")]
        if not pids:
            return []
        try:
            details = await asyncio.gather(
                *[self.maps.get_place_details(p) for p in pids], return_exceptions=True
            )
        except Exception as e:
            logger.warning("Review fetch failed", error=str(e))
            return []
        reviews: list[dict] = []
        for d in details:
            if isinstance(d, dict):
                for r in d.get("reviews", []) or []:
                    if isinstance(r, dict) and r.get("text"):
                        reviews.append({"text": r.get("text", ""), "rating": r.get("rating", 3)})
        return reviews

    # ---- small utilities --------------------------------------------------

    @staticmethod
    def _ok(d: Any) -> bool:
        return isinstance(d, dict) and bool(d) and "error" not in d

    @staticmethod
    def _parse_state(formatted: str | None) -> str | None:
        m = _STATE_RE.search(formatted or "")
        return m.group(1) if m else None

    @staticmethod
    def _parse_city(formatted: str | None, geography: dict) -> str | None:
        parts = [p.strip() for p in (formatted or "").split(",") if p.strip()]
        # e.g. "500 W 2nd St, Austin, TX 78701, USA" -> city is third from the end
        if len(parts) >= 3:
            return parts[-3]
        county = (geography or {}).get("county", "")
        return county.replace(" County", "").strip() or None

    async def _safe(self, coro, default, label: str):
        try:
            return await asyncio.wait_for(coro, timeout=60)
        except Exception as e:
            logger.warning(
                "Feasibility leg failed", leg=label, error=str(e), error_type=type(e).__name__
            )
            return default

    def _safe_sync(self, fn, *args, default, label: str):
        try:
            return fn(*args)
        except Exception as e:
            logger.warning(
                "Feasibility leg failed", leg=label, error=str(e), error_type=type(e).__name__
            )
            return default

    async def _progress(self, report_id: str, step: int, label: str) -> None:
        try:
            await self.repo.update(
                report_id, {"progress": {"step": step, "steps_total": _STEPS_TOTAL, "label": label}}
            )
        except Exception:
            pass
