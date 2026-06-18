"""Daily Brief — the morning surface that makes PHOW a daily habit.

Distills the day's Business Radar alerts (news + competitor moves + reputation) into a
single AI-synthesized briefing: a pulse (calm / watch / alert), a short narrative, the
prioritized highlights, and the top 1-3 actions to take today. One brief per business
per day; the morning beat dispatcher pre-generates it, and "Generate now" refreshes it.

Synthesis is one LLM call with a deterministic fallback, so a brief always exists.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client

from ..core.llm import get_llm_service
from ..core.logging import get_logger
from ..repositories.daily_brief_repository import DailyBriefRepository
from ..repositories.radar_repository import RadarRepository
from ..repositories.business_profile_repository import BusinessProfileRepository

logger = get_logger("daily_brief_service")

_SEVERITY_RANK = {"urgent": 3, "watch": 2, "info": 1}
_MAX_HIGHLIGHTS = 6
_MAX_ACTIONS = 3


class DailyBriefService:
    def __init__(self, db: Client):
        self.db = db
        self.repo = DailyBriefRepository(db)
        self.radar_repo = RadarRepository(db)
        self.profile_repo = BusinessProfileRepository(db)
        self.llm = get_llm_service()

    # ---- read -------------------------------------------------------------

    async def get_latest(self, business_profile_id: str) -> dict[str, Any]:
        brief = await self.repo.get_latest(business_profile_id)
        has_today = bool(brief and brief.get("brief_date") == self.repo.today())
        return {"brief": brief, "has_today": has_today}

    async def get_due_profile_ids(self) -> list[str]:
        """Business profiles (with an active radar) that have no brief yet today."""
        subs = await self.radar_repo.list_active_subscriptions()
        today = self.repo.today()
        due: list[str] = []
        for s in subs:
            bp = s.get("business_profile_id")
            if bp and not await self.repo.exists_for_date(bp, today):
                due.append(bp)
        return due

    # ---- generate ---------------------------------------------------------

    async def generate(self, business_profile_id: str, window_hours: int = 30) -> dict[str, Any]:
        profile = await self.profile_repo.get_by_id(business_profile_id)
        if not profile:
            raise ValueError("Business profile not found")

        since = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()
        alerts = await self.radar_repo.recent_alerts(business_profile_id, since, limit=60)

        highlights = self._rank_highlights(alerts)
        stats = self._compute_stats(alerts)
        pulse = self._compute_pulse(alerts)
        body = await self._synthesize(profile, highlights, stats, pulse)

        record = {
            "business_profile_id": business_profile_id,
            "session_id": profile.get("session_id"),
            "user_id": profile.get("user_id"),
            "brief_date": self.repo.today(),
            "pulse": pulse,
            "headline": body["headline"],
            "narrative": body["narrative"],
            "highlights": highlights,
            "top_actions": body["top_actions"],
            "stats": stats,
            "alert_ids": [a.get("id") for a in alerts if a.get("id")],
        }
        saved = await self.repo.upsert(record)
        try:
            from .action_inbox_service import ActionInboxService

            await ActionInboxService(self.db).seed_from_brief(saved)
        except Exception as e:
            logger.warning("Action inbox seeding failed", error=str(e))
        logger.info(
            "Daily brief generated",
            business_profile_id=business_profile_id,
            pulse=pulse,
            alerts=stats["alerts_total"],
        )
        return saved

    # ---- synthesis (LLM + deterministic fallback) -------------------------

    async def _synthesize(
        self, profile: dict, highlights: list[dict], stats: dict, pulse: str
    ) -> dict[str, Any]:
        if not highlights:
            return self._fallback_brief(profile, highlights, stats, pulse)

        listing = "\n".join(
            f"{i}. [{h.get('severity')}/{h.get('category')}] {h.get('title')}"
            f" — {h.get('why_it_matters') or ''}"
            for i, h in enumerate(highlights)
        )
        prompt = f"""You are the morning analyst for a small business owner. Given the business and today's prioritized signals, write a short, punchy morning brief.

BUSINESS:
{self._business_context(profile)}

TODAY'S SIGNALS (most important first):
{listing}

Respond ONLY with valid JSON in this exact shape:
{{"headline": "one tight sentence capturing the day", "narrative": "2-3 sentences on what changed and what it means for THIS business", "top_actions": ["concrete action", "concrete action"]}}

Rules:
- Speak directly to the owner ("you"). Be specific and practical — no fluff, no hedging.
- 1-3 top_actions ordered by priority; if nothing truly needs action, return [].
- Ground every claim in the signals above; do not invent facts."""

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a sharp small-business analyst. Respond only with valid JSON.",
            )
            parsed = json.loads(self._strip_fences(response))
            headline = (parsed.get("headline") or "").strip()
            narrative = (parsed.get("narrative") or "").strip()
            actions = [
                a.strip()
                for a in (parsed.get("top_actions") or [])
                if isinstance(a, str) and a.strip()
            ][:_MAX_ACTIONS]
            if not headline or not narrative:
                raise ValueError("incomplete brief")
            return {
                "headline": headline[:300],
                "narrative": narrative[:1200],
                "top_actions": actions or self._select_top_actions(highlights),
            }
        except Exception as e:
            logger.warning("Daily brief synthesis failed, using fallback", error=str(e))
            return self._fallback_brief(profile, highlights, stats, pulse)

    @classmethod
    def _fallback_brief(
        cls, profile: dict, highlights: list[dict], stats: dict, pulse: str
    ) -> dict[str, Any]:
        name = profile.get("business_name") or cls._humanize(
            profile.get("business_type") or "your business"
        )
        if stats["alerts_total"] == 0:
            return {
                "headline": "All clear — no new signals today.",
                "narrative": (
                    f"Nothing notable surfaced for {name} in the last day. A calm day is a "
                    "good day — consider one proactive move like replying to a recent review "
                    "or checking your top competitor's rating."
                ),
                "top_actions": [],
            }
        parts = []
        if stats["urgent"]:
            parts.append(f"{stats['urgent']} urgent")
        if stats["watch"]:
            parts.append(f"{stats['watch']} to watch")
        summary = " and ".join(parts) or f"{stats['alerts_total']} update(s)"
        top = highlights[0]
        return {
            "headline": f"{summary.capitalize()} for {name} today.",
            "narrative": top.get("why_it_matters") or top.get("title") or "Review today's signals.",
            "top_actions": cls._select_top_actions(highlights),
        }

    # ---- pure helpers (unit-tested) ---------------------------------------

    @classmethod
    def _rank_highlights(cls, alerts: list[dict]) -> list[dict]:
        ranked = sorted(
            alerts,
            key=lambda a: (
                _SEVERITY_RANK.get(a.get("severity"), 0),
                a.get("relevance_score") or 0,
            ),
            reverse=True,
        )
        return [cls._highlight(a) for a in ranked[:_MAX_HIGHLIGHTS]]

    @staticmethod
    def _highlight(a: dict) -> dict:
        return {
            "alert_id": a.get("id"),
            "title": a.get("title"),
            "category": a.get("category"),
            "severity": a.get("severity"),
            "why_it_matters": a.get("why_it_matters"),
            "suggested_action": a.get("suggested_action"),
            "url": a.get("url"),
        }

    @staticmethod
    def _compute_stats(alerts: list[dict]) -> dict[str, int]:
        return {
            "alerts_total": len(alerts),
            "urgent": sum(1 for a in alerts if a.get("severity") == "urgent"),
            "watch": sum(1 for a in alerts if a.get("severity") == "watch"),
            "competitor_moves": sum(1 for a in alerts if a.get("category") == "competition"),
            "new_reviews": sum(1 for a in alerts if a.get("category") == "reputation"),
        }

    @staticmethod
    def _compute_pulse(alerts: list[dict]) -> str:
        severities = {a.get("severity") for a in alerts}
        if "urgent" in severities:
            return "alert"
        if "watch" in severities:
            return "watch"
        return "calm"

    @staticmethod
    def _select_top_actions(highlights: list[dict]) -> list[str]:
        actions: list[str] = []
        seen: set[str] = set()
        for h in highlights:
            act = (h.get("suggested_action") or "").strip()
            if act and act.lower() not in seen:
                seen.add(act.lower())
                actions.append(act)
            if len(actions) >= _MAX_ACTIONS:
                break
        return actions

    @staticmethod
    def _business_context(profile: dict) -> str:
        parts = [f"Type: {DailyBriefService._humanize(profile.get('business_type') or 'business')}"]
        for key, label in (
            ("business_name", "Name"),
            ("location_address", "Location"),
            ("business_description", "About"),
            ("target_customers", "Customers"),
        ):
            if profile.get(key):
                parts.append(f"{label}: {profile[key]}")
        return "\n".join(parts)

    @staticmethod
    def _humanize(value: str) -> str:
        return (value or "").replace("_", " ").strip()

    @staticmethod
    def _strip_fences(text: str) -> str:
        t = (text or "").strip()
        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
            t = re.sub(r"\n?```$", "", t)
        return t.strip()
