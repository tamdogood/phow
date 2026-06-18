"""Tests for DailyBriefService pure logic: ranking, pulse, stats, actions, fallback."""

from app.services.daily_brief_service import DailyBriefService


def _alert(severity="info", category="macro", score=50, **kw):
    return {
        "id": kw.get("id", "a1"),
        "title": kw.get("title", "Some headline"),
        "category": category,
        "severity": severity,
        "relevance_score": score,
        "why_it_matters": kw.get("why", "It matters."),
        "suggested_action": kw.get("action", "Do something."),
        "url": kw.get("url"),
    }


class TestPulse:
    def test_alert_when_any_urgent(self):
        assert DailyBriefService._compute_pulse([_alert("info"), _alert("urgent")]) == "alert"

    def test_watch_when_watch_no_urgent(self):
        assert DailyBriefService._compute_pulse([_alert("watch"), _alert("info")]) == "watch"

    def test_calm_when_only_info(self):
        assert DailyBriefService._compute_pulse([_alert("info")]) == "calm"

    def test_calm_when_empty(self):
        assert DailyBriefService._compute_pulse([]) == "calm"


class TestRankHighlights:
    def test_orders_by_severity_then_relevance(self):
        alerts = [
            _alert("info", score=90, id="info90"),
            _alert("urgent", score=10, id="urgent10"),
            _alert("watch", score=80, id="watch80"),
        ]
        ranked = DailyBriefService._rank_highlights(alerts)
        assert [h["alert_id"] for h in ranked] == ["urgent10", "watch80", "info90"]

    def test_caps_at_six(self):
        alerts = [_alert("info", id=str(i)) for i in range(10)]
        assert len(DailyBriefService._rank_highlights(alerts)) == 6

    def test_highlight_shape(self):
        h = DailyBriefService._rank_highlights([_alert(category="reputation")])[0]
        assert set(h) == {
            "alert_id",
            "title",
            "category",
            "severity",
            "why_it_matters",
            "suggested_action",
            "url",
        }


class TestStats:
    def test_counts_by_severity_and_category(self):
        alerts = [
            _alert("urgent", "competition"),
            _alert("watch", "reputation"),
            _alert("info", "macro"),
        ]
        assert DailyBriefService._compute_stats(alerts) == {
            "alerts_total": 3,
            "urgent": 1,
            "watch": 1,
            "competitor_moves": 1,
            "new_reviews": 1,
        }


class TestTopActions:
    def test_dedups_case_insensitive_and_caps_three(self):
        hs = [
            {"suggested_action": "Reply to reviews"},
            {"suggested_action": "reply to reviews"},
            {"suggested_action": "Check competitor"},
            {"suggested_action": "Run a promo"},
            {"suggested_action": "Adjust pricing"},
        ]
        assert DailyBriefService._select_top_actions(hs) == [
            "Reply to reviews",
            "Check competitor",
            "Run a promo",
        ]

    def test_skips_blank(self):
        hs = [{"suggested_action": ""}, {"suggested_action": "  "}, {"suggested_action": "Do X"}]
        assert DailyBriefService._select_top_actions(hs) == ["Do X"]


class TestFallbackBrief:
    def test_calm_day_has_no_actions(self):
        profile = {"business_name": "Blue Bottle", "business_type": "coffee_shop"}
        stats = {
            "alerts_total": 0,
            "urgent": 0,
            "watch": 0,
            "competitor_moves": 0,
            "new_reviews": 0,
        }
        body = DailyBriefService._fallback_brief(profile, [], stats, "calm")
        assert "All clear" in body["headline"]
        assert body["top_actions"] == []
        assert "Blue Bottle" in body["narrative"]

    def test_busy_day_summarizes_and_carries_actions(self):
        profile = {"business_type": "coffee_shop"}
        alerts = [
            _alert("urgent", "competition", 90, action="Counter the new opening"),
            _alert("watch", "reputation", 70, action="Reply to reviews"),
        ]
        highlights = DailyBriefService._rank_highlights(alerts)
        stats = DailyBriefService._compute_stats(alerts)
        body = DailyBriefService._fallback_brief(profile, highlights, stats, "alert")
        assert "urgent" in body["headline"].lower()
        assert "coffee shop" in body["headline"]  # humanized business_type
        assert body["top_actions"]
