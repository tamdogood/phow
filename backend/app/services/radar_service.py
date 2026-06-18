"""Business Radar — per-business monitoring of news/events that could affect a business.

Pipeline (run_scan): build watch topics from the business profile -> collect candidate
news (GDELT) -> dedupe by URL/title -> LLM triage (category / severity / why-it-matters /
suggested-action, with a deterministic fallback) -> persist prioritized alerts.

Signal sources are pluggable; the MVP ships the GDELT news collector (competitor names are
folded into the watch topics so competitor news surfaces too). Places-based competitor-move
diffing and local/macro collectors are the documented next additions.
"""

import asyncio
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client

from ..core.logging import get_logger
from ..core.llm import get_llm_service
from ..core import plans
from ..repositories.radar_repository import RadarRepository
from ..repositories.business_profile_repository import (
    BusinessProfileRepository,
    TrackedCompetitorRepository,
)
from ..tools.market_research.gdelt_client import get_gdelt_client

logger = get_logger("radar_service")

_STATE_RE = re.compile(r",\s*([A-Z]{2})\s+\d{5}")
_CATEGORIES = {"competition", "regulation", "supply", "demand", "macro", "local", "reputation"}
_SEVERITIES = {"info", "watch", "urgent"}
_MAX_CANDIDATES = 25
_RELEVANCE_FLOOR = 40

# F&B input costs to watch (FRED series). Monthly CPI/avg-price series; IDs are tunable.
_FNB_COST_SERIES = [
    ("Coffee", "APU0000717311", "$/lb"),
    ("Ground beef", "APU0000703112", "$/lb"),
    ("Eggs", "APU0000708111", "$/doz"),
    ("Bread", "APU0000702111", "$/lb"),
    ("Chicken", "APU0000706111", "$/lb"),
    ("Electricity", "APU000072610", "$/kWh"),
]
_FNB_KEYWORDS = (
    "restaurant",
    "cafe",
    "coffee",
    "food",
    "bar",
    "bakery",
    "grill",
    "pizza",
    "kitchen",
    "eatery",
    "diner",
    "brew",
    "deli",
    "bistro",
)


class RadarService:
    """Orchestrates radar subscriptions, scans, and the alert feed."""

    def __init__(self, db: Client):
        self.db = db
        self.repo = RadarRepository(db)
        self.profile_repo = BusinessProfileRepository(db)
        self.competitor_repo = TrackedCompetitorRepository(db)
        self.llm = get_llm_service()

    # ---- subscriptions / feed --------------------------------------------

    async def get_or_create_for_profile(self, business_profile_id: str) -> dict[str, Any]:
        existing = await self.repo.get_subscription_by_profile(business_profile_id)
        if existing:
            return existing
        profile = await self.profile_repo.get_by_id(business_profile_id)
        if not profile:
            raise ValueError("Business profile not found")
        competitors = await self.competitor_repo.get_competitors(business_profile_id)
        topics = self._build_watch_topics(profile, competitors)
        name = profile.get("business_name") or self._humanize(
            profile.get("business_type", "business")
        )
        return await self.repo.create_subscription(
            {
                "business_profile_id": business_profile_id,
                "session_id": profile.get("session_id"),
                "user_id": profile.get("user_id"),
                "name": f"{name} Radar",
                "watch_topics": topics,
                "status": "active",
            }
        )

    async def update_subscription(
        self, business_profile_id: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        sub = await self.get_or_create_for_profile(business_profile_id)
        clean = {k: v for k, v in fields.items() if v is not None}
        if not clean:
            return sub
        return await self.repo.update_subscription(sub["id"], clean)

    async def get_feed(
        self, business_profile_id: str, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        sub = await self.repo.get_subscription_by_profile(business_profile_id)
        alerts = await self.repo.list_alerts(business_profile_id, status, limit, offset)
        unread = await self.repo.count_unread(business_profile_id)
        latest_scan = await self.repo.latest_scan(sub["id"]) if sub else None
        return {
            "subscription": sub,
            "alerts": alerts,
            "unread_count": unread,
            "latest_scan": latest_scan,
        }

    async def mark_alert(self, alert_id: str, status: str) -> dict[str, Any] | None:
        if status not in {"new", "read", "dismissed"}:
            raise ValueError("Invalid status")
        return await self.repo.mark_alert(alert_id, status)

    async def trigger_scan(self, business_profile_id: str) -> dict[str, Any]:
        sub = await self.get_or_create_for_profile(business_profile_id)
        try:
            from ..workers.radar_tasks import run_radar_scan

            run_radar_scan.delay(sub["id"])
        except Exception as e:
            logger.warning("Failed to dispatch radar scan", subscription_id=sub["id"], error=str(e))
        return {"subscription_id": sub["id"], "status": "running"}

    async def get_due_subscription_ids(self) -> list[str]:
        """IDs of active subscriptions due for a scan (used by the beat dispatcher)."""
        subs = await self.repo.list_active_subscriptions()
        now = datetime.now(timezone.utc)
        return [s["id"] for s in subs if self._is_due(s, now)]

    @staticmethod
    def _is_due(sub: dict, now: datetime) -> bool:
        interval = timedelta(days=7) if sub.get("frequency") == "weekly" else timedelta(hours=20)
        last = RadarService._parse_dt(sub.get("last_scanned_at"))
        return last is None or now - last >= interval

    # ---- scan pipeline (called by the Celery worker) ----------------------

    async def run_scan(self, subscription_id: str) -> None:
        sub = await self.repo.get_subscription(subscription_id)
        if not sub:
            logger.error("Radar subscription not found", subscription_id=subscription_id)
            return
        scan = await self.repo.create_scan(subscription_id)
        scan_id = scan.get("id")
        try:
            profile = await self.profile_repo.get_by_id(sub["business_profile_id"]) or {}

            candidates = await self._safe(self._collect_gdelt(sub), [], "gdelt")
            seen_urls = await self.repo.recent_alert_urls(subscription_id)
            candidates = self._dedupe(candidates, seen_urls)[:_MAX_CANDIDATES]

            assessed = await self._triage(profile, candidates)
            signals = await self._safe(self._collect_signal_alerts(sub, profile), [], "signals")
            assessed = assessed + signals

            active_categories = set(sub.get("categories") or [])
            alerts = []
            for a in assessed:
                if active_categories and a["category"] not in active_categories:
                    continue
                alerts.append(
                    {
                        "id": str(uuid.uuid4()),
                        "subscription_id": subscription_id,
                        "business_profile_id": sub["business_profile_id"],
                        "scan_id": scan_id,
                        "title": (a.get("title") or "")[:500],
                        "url": a.get("url"),
                        "source": a.get("source"),
                        "source_domain": a.get("source_domain"),
                        "published_at": a.get("published_at"),
                        "category": a["category"],
                        "severity": a["severity"],
                        "relevance_score": a["relevance_score"],
                        "summary": a.get("summary"),
                        "why_it_matters": a.get("why_it_matters"),
                        "suggested_action": a.get("suggested_action"),
                        "status": "new",
                        "raw": a.get("raw"),
                    }
                )

            await self.repo.save_alerts(alerts)
            await self.repo.update_scan(
                scan_id,
                {
                    "status": "completed",
                    "candidates_found": len(candidates) + len(signals),
                    "alerts_created": len(alerts),
                    "completed_at": self._now(),
                },
            )
            await self.repo.update_subscription(subscription_id, {"last_scanned_at": self._now()})
            logger.info(
                "Radar scan completed",
                subscription_id=subscription_id,
                candidates=len(candidates),
                alerts=len(alerts),
            )
        except Exception as e:
            logger.error(
                "Radar scan failed",
                subscription_id=subscription_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            await self.repo.update_scan(
                scan_id, {"status": "failed", "error": str(e), "completed_at": self._now()}
            )

    # ---- collectors -------------------------------------------------------

    async def _collect_gdelt(self, sub: dict) -> list[dict]:
        topics = (sub.get("watch_topics") or [])[:10]
        if not topics:
            return []
        days = 8 if sub.get("frequency") == "weekly" else 3
        res = await get_gdelt_client().search_industry_news(topics, days_back=days, max_records=50)
        articles = res.get("articles", []) if isinstance(res, dict) else []
        out: list[dict] = []
        for a in articles:
            if not a.get("title") or not a.get("url"):
                continue
            out.append(
                {
                    "title": a["title"],
                    "url": a["url"],
                    "source": "gdelt",
                    "source_domain": a.get("source"),
                    "published_at": self._parse_gdelt_date(a.get("date")),
                    "raw": {"language": a.get("language"), "country": a.get("source_country")},
                }
            )
        return out

    # ---- structured-signal collectors (competitor moves + reputation) -----

    async def _collect_signal_alerts(self, sub: dict, profile: dict) -> list[dict]:
        """Pre-triaged alerts from owned signals: competitor moves + your reputation.

        These are structured diffs (not headlines), so they skip the news LLM and carry
        their own category/severity. Each diff only fires on a real change and rolls the
        baseline forward, so they self-dedupe across scans.
        """
        out: list[dict] = []
        out += await self._safe(self._collect_competitor_moves(sub), [], "competitor_moves")
        out += await self._safe(self._collect_reputation(sub, profile), [], "reputation")
        if plans.has_feature(profile.get("plan"), "cost_radar"):
            out += await self._safe(self._collect_cost_signals(profile), [], "cost")
        return out

    async def _collect_cost_signals(self, profile: dict) -> list[dict]:
        """Margin Defender: flag material month-over-month swings in F&B input costs (FRED)."""
        bt = (profile.get("business_type") or "").lower()
        if not any(k in bt for k in _FNB_KEYWORDS):
            return []
        from ..tools.market_research.fred_client import FREDClient

        client = FREDClient()
        out: list[dict] = []
        try:
            for label, series_id, unit in _FNB_COST_SERIES:
                data = await client.get_series(series_id, limit=2)
                obs = data.get("observations") if isinstance(data, dict) else None
                if not obs or len(obs) < 2:
                    continue
                alert = self._cost_alert(label, obs[0].get("value"), obs[1].get("value"), unit)
                if alert:
                    out.append(alert)
        finally:
            await client.close()
        return out

    @staticmethod
    def _cost_alert(
        label: str, latest: float | None, prior: float | None, unit: str
    ) -> dict | None:
        """Pure: emit a supply alert when an input cost moves >=5% month-over-month."""
        if not latest or not prior:
            return None
        change = (latest - prior) / prior
        if abs(change) < 0.05:
            return None
        pct = round(change * 100, 1)
        up = change > 0
        severity = "watch" if abs(change) >= 0.10 else "info"
        score = min(90, 50 + int(abs(pct)))
        direction = "up" if up else "down"
        title = f"{label} prices {direction} {abs(pct)}% month-over-month"
        if up:
            why = "Rising input costs squeeze your already-thin margins — pricing or portions may need a look."
            action = (
                f"Review your {label.lower()}-heavy items and adjust price, portion, or supplier."
            )
        else:
            why = "Falling input costs are a chance to widen margin or run a promotion."
            action = f"Lock in lower {label.lower()} costs or feature {label.lower()}-based items."
        return RadarService._signal(
            "supply",
            severity,
            score,
            title,
            why,
            action,
            source="fred",
            raw={"label": label, "latest": latest, "prior": prior, "pct": pct, "unit": unit},
        )

    async def _collect_competitor_moves(self, sub: dict) -> list[dict]:
        competitors = await self.competitor_repo.get_competitors(sub["business_profile_id"])
        if not competitors:
            return []
        from ..tools.location_scout.google_maps import GoogleMapsClient

        maps = GoogleMapsClient()
        out: list[dict] = []
        for comp in competitors[:10]:
            place_id = comp.get("place_id")
            if not place_id:
                continue
            details = await maps.get_place_details(place_id)
            if not details:
                continue
            current = {
                "rating": details.get("rating"),
                "review_count": details.get("user_ratings_total"),
                "business_status": details.get("business_status"),
            }
            alert = self._diff_competitor(comp, current)
            await self.competitor_repo.update_competitor(
                comp["id"],
                rating=current["rating"],
                review_count=current["review_count"],
                business_status=current["business_status"],
            )
            if alert:
                out.append(alert)
        return out

    async def _collect_reputation(self, sub: dict, profile: dict) -> list[dict]:
        place_id = profile.get("location_place_id")
        if not place_id:
            return []
        from ..tools.location_scout.google_maps import GoogleMapsClient

        details = await GoogleMapsClient().get_place_details(place_id)
        if not details:
            return []
        current = {
            "rating": details.get("rating"),
            "review_count": details.get("user_ratings_total"),
        }
        if current["rating"] is None and current["review_count"] is None:
            return []
        last = await self.repo.last_alert_by_category(sub["id"], "reputation")
        alert = self._reputation_alert(profile, current, (last or {}).get("raw"))
        return [alert] if alert else []

    @staticmethod
    def _diff_competitor(prev: dict, current: dict) -> dict | None:
        """Pure diff: a tracked competitor's stored snapshot vs fresh Places data."""
        name = prev.get("name") or "A tracked competitor"
        prev_status, cur_status = prev.get("business_status"), current.get("business_status")
        if cur_status and cur_status != "OPERATIONAL" and prev_status in (None, "OPERATIONAL"):
            return RadarService._signal(
                "competition",
                "urgent",
                85,
                f"{name} appears to have closed",
                "A nearby competitor closing frees up demand you can capture.",
                f"Target {name}'s former customers with a promo or local post this week.",
                raw=current,
            )
        prev_rating, cur_rating = prev.get("rating"), current.get("rating")
        if prev_rating and cur_rating:
            delta = round(cur_rating - prev_rating, 2)
            if delta <= -0.3:
                return RadarService._signal(
                    "competition",
                    "watch",
                    70,
                    f"{name}'s rating slipped {prev_rating}→{cur_rating}",
                    "A weakening competitor is an opening to win their unhappy customers.",
                    f"Read {name}'s recent 1-2★ reviews and beat them where they fall short.",
                    raw=current,
                )
            if delta >= 0.3:
                return RadarService._signal(
                    "competition",
                    "info",
                    55,
                    f"{name}'s rating climbed {prev_rating}→{cur_rating}",
                    "A rising rival may be pulling share — worth understanding why.",
                    f"Check what {name} is doing well lately and match it.",
                    raw=current,
                )
        prev_reviews, cur_reviews = prev.get("review_count"), current.get("review_count")
        if prev_reviews and cur_reviews and cur_reviews - prev_reviews >= 25:
            return RadarService._signal(
                "competition",
                "info",
                55,
                f"{name} gained {cur_reviews - prev_reviews} reviews",
                "A surge in reviews usually signals a promo, press, or viral moment.",
                f"See what's driving {name}'s traffic and consider a counter-move.",
                raw=current,
            )
        return None

    @staticmethod
    def _reputation_alert(profile: dict, current: dict, prior: dict | None) -> dict | None:
        """Pure diff: your own Google rating/review count vs the last reputation snapshot."""
        rating, reviews = current.get("rating"), current.get("review_count")
        if not prior:
            return RadarService._signal(
                "reputation",
                "info",
                60,
                f"Now tracking your Google rating ({rating or 'n/a'}★, {reviews or 0} reviews)",
                "Your rating and review velocity are your daily reputation pulse.",
                "Make replying to new reviews a daily habit — it lifts your ranking.",
                raw=current,
            )
        p_rating, p_reviews = prior.get("rating"), prior.get("review_count")
        if rating and p_rating and round(rating - p_rating, 2) <= -0.2:
            return RadarService._signal(
                "reputation",
                "watch",
                80,
                f"Your rating dropped {p_rating}→{rating}",
                "A dip costs you map ranking and walk-ins, and compounds if unaddressed.",
                "Read your newest reviews and respond to every negative one today.",
                raw=current,
            )
        new_reviews = (reviews or 0) - (p_reviews or 0)
        if new_reviews >= 1:
            return RadarService._signal(
                "reputation",
                "info",
                65,
                f"You have {new_reviews} new review(s) — now {reviews} ({rating or 'n/a'}★)",
                "Fresh reviews are your reputation pulse, and replying lifts your ranking.",
                "Reply to each new review today — thank the positive, recover the negative.",
                raw=current,
            )
        if rating and p_rating and round(rating - p_rating, 2) >= 0.2:
            return RadarService._signal(
                "reputation",
                "info",
                55,
                f"Your rating climbed {p_rating}→{rating}",
                "Momentum on your rating directly improves discovery and conversion.",
                "Thank recent reviewers and keep the streak going.",
                raw=current,
            )
        return None

    @staticmethod
    def _signal(
        category: str,
        severity: str,
        score: int,
        title: str,
        why: str,
        action: str,
        *,
        source: str = "places",
        url: str | None = None,
        raw: dict | None = None,
    ) -> dict:
        """Build a ready-to-persist alert from a structured signal (no LLM triage)."""
        return {
            "title": title,
            "url": url,
            "source": source,
            "source_domain": None,
            "published_at": None,
            "category": category,
            "severity": severity,
            "relevance_score": score,
            "summary": title,
            "why_it_matters": why,
            "suggested_action": action,
            "raw": raw,
        }

    # ---- LLM triage -------------------------------------------------------

    async def _triage(self, profile: dict, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return []
        context = self._business_context(profile)
        listing = "\n".join(
            f"{i}. {c.get('title')} — ({c.get('source_domain') or c.get('source')})"
            for i, c in enumerate(candidates)
        )
        prompt = f"""You are a vigilant analyst for a small business owner. Below is the business and a numbered list of recent news headlines. For EACH headline, decide whether it could realistically affect THIS business, and if so how.

BUSINESS:
{context}

HEADLINES:
{listing}

Respond ONLY with valid JSON in this exact shape:
{{"alerts": [{{"i": <headline number>, "relevant": true|false, "category": "competition|regulation|supply|demand|macro|local|reputation", "severity": "info|watch|urgent", "relevance_score": 0-100, "summary": "one neutral sentence", "why_it_matters": "one sentence on the concrete impact to THIS business", "suggested_action": "one concrete next step"}}]}}

Rules:
- Only include headlines that are plausibly relevant (relevant=true). Skip generic/unrelated news.
- severity: "urgent" = act this week; "watch" = monitor; "info" = context only.
- Be specific to this business's type and location. Keep each field to one sentence."""

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a market intelligence analyst. Respond only with valid JSON.",
            )
            parsed = json.loads(self._strip_fences(response))
            assessed = []
            for item in parsed.get("alerts", []):
                idx = item.get("i")
                if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
                    continue
                if not item.get("relevant"):
                    continue
                score = int(item.get("relevance_score", 0) or 0)
                if score < _RELEVANCE_FLOOR:
                    continue
                cand = candidates[idx]
                assessed.append(
                    {
                        **cand,
                        "category": (
                            item.get("category") if item.get("category") in _CATEGORIES else "macro"
                        ),
                        "severity": (
                            item.get("severity") if item.get("severity") in _SEVERITIES else "info"
                        ),
                        "relevance_score": max(0, min(100, score)),
                        "summary": (item.get("summary") or cand.get("title"))[:600],
                        "why_it_matters": (item.get("why_it_matters") or "")[:600],
                        "suggested_action": (item.get("suggested_action") or "")[:600],
                    }
                )
            return assessed
        except Exception as e:
            logger.warning("Radar triage LLM failed, using fallback", error=str(e))
            return self._fallback_triage(candidates)

    @staticmethod
    def _fallback_triage(candidates: list[dict]) -> list[dict]:
        out = []
        for cand in candidates[:8]:
            out.append(
                {
                    **cand,
                    "category": "macro",
                    "severity": "info",
                    "relevance_score": 50,
                    "summary": cand.get("title"),
                    "why_it_matters": "Flagged from your watch topics — review to see if it affects you.",
                    "suggested_action": "Open the article to assess relevance.",
                }
            )
        return out

    # ---- helpers ----------------------------------------------------------

    @staticmethod
    def _build_watch_topics(profile: dict, competitors: list[dict]) -> list[str]:
        bt = RadarService._humanize(profile.get("business_type") or "small business")
        city = RadarService._parse_city(profile.get("location_address"))
        state = RadarService._parse_state(profile.get("location_address"))
        name = profile.get("business_name")
        topics: list[str] = [bt]
        if city:
            topics += [f"{bt} {city}", f"{city} small business"]
        if state:
            topics.append(f"{state} minimum wage")
        topics += [f"{bt} regulation", f"{bt} prices", "food costs inflation"]
        if name:
            topics.append(name)
        for c in (competitors or [])[:3]:
            if c.get("name"):
                topics.append(c["name"])
        seen: set[str] = set()
        out: list[str] = []
        for t in topics:
            t = (t or "").strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                out.append(t)
        return out[:12]

    @staticmethod
    def _business_context(profile: dict) -> str:
        parts = [
            f"Type: {RadarService._humanize(profile.get('business_type') or 'small business')}"
        ]
        if profile.get("business_name"):
            parts.append(f"Name: {profile['business_name']}")
        if profile.get("location_address"):
            parts.append(f"Location: {profile['location_address']}")
        if profile.get("business_description"):
            parts.append(f"About: {profile['business_description']}")
        if profile.get("target_customers"):
            parts.append(f"Customers: {profile['target_customers']}")
        return "\n".join(parts)

    @staticmethod
    def _dedupe(candidates: list[dict], seen_urls: set[str]) -> list[dict]:
        out: list[dict] = []
        urls = set(seen_urls)
        titles: set[str] = set()
        for c in candidates:
            url = (c.get("url") or "").split("?")[0]
            title_key = re.sub(r"\W+", "", (c.get("title") or "").lower())[:80]
            if not url or url in urls or title_key in titles:
                continue
            urls.add(url)
            titles.add(title_key)
            out.append(c)
        return out

    @staticmethod
    def _humanize(value: str) -> str:
        return (value or "").replace("_", " ").strip()

    @staticmethod
    def _parse_state(address: str | None) -> str | None:
        m = _STATE_RE.search(address or "")
        return m.group(1) if m else None

    @staticmethod
    def _parse_city(address: str | None) -> str | None:
        parts = [p.strip() for p in (address or "").split(",") if p.strip()]
        return parts[-3] if len(parts) >= 3 else None

    @staticmethod
    def _parse_gdelt_date(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return (
                datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
            )
        except Exception:
            return None

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    @staticmethod
    def _strip_fences(text: str) -> str:
        t = (text or "").strip()
        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
            t = re.sub(r"\n?```$", "", t)
        return t.strip()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _safe(self, coro, default, label: str):
        try:
            return await asyncio.wait_for(coro, timeout=90)
        except Exception as e:
            logger.warning("Radar collector failed", collector=label, error=str(e))
            return default
