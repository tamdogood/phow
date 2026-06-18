"""Tests for RadarService pure logic: topics, dedupe, fallback, due-check, signal diffs."""

from datetime import datetime, timedelta, timezone

from app.services.radar_service import RadarService


class TestWatchTopics:
    def test_includes_type_city_name_competitors(self):
        profile = {
            "business_type": "coffee_shop",
            "location_address": "500 W 2nd St, Austin, TX 78701, USA",
            "business_name": "Bean There",
        }
        comps = [{"name": "Competitor Cafe"}, {"name": "Rival Roasters"}]
        topics = RadarService._build_watch_topics(profile, comps)
        assert "coffee shop" in topics
        assert any("Austin" in t for t in topics)
        assert "Bean There" in topics
        assert "Competitor Cafe" in topics
        assert len(topics) <= 12

    def test_dedupes_case_insensitive(self):
        topics = RadarService._build_watch_topics({"business_type": "cafe"}, [])
        assert len(topics) == len({t.lower() for t in topics})


class TestDedupe:
    def test_drops_seen_urls_and_duplicate_titles(self):
        cands = [
            {"url": "http://a.com/1?x=1", "title": "Big News"},
            {"url": "http://a.com/1?x=2", "title": "Different"},  # same url base
            {"url": "http://b.com/2", "title": "big news!!"},  # same title key
            {"url": "http://c.com/3", "title": "Fresh"},
        ]
        out = RadarService._dedupe(cands, set())
        assert {c["title"] for c in out} == {"Big News", "Fresh"}

    def test_respects_seen_urls(self):
        cands = [{"url": "http://a.com/1", "title": "X"}]
        assert RadarService._dedupe(cands, {"http://a.com/1"}) == []


class TestFallbackTriage:
    def test_assigns_defaults_and_caps_at_eight(self):
        cands = [{"title": f"t{i}", "url": f"u{i}"} for i in range(12)]
        out = RadarService._fallback_triage(cands)
        assert len(out) == 8
        assert all(o["category"] == "macro" and o["severity"] == "info" for o in out)
        assert all(o["relevance_score"] == 50 for o in out)
        assert all(o["why_it_matters"] and o["suggested_action"] for o in out)


class TestGdeltDate:
    def test_parses_valid(self):
        assert RadarService._parse_gdelt_date("20260615T130000Z").startswith("2026-06-15T13:00:00")

    def test_none_on_bad_input(self):
        assert RadarService._parse_gdelt_date("nonsense") is None
        assert RadarService._parse_gdelt_date(None) is None


class TestIsDue:
    def test_never_scanned_is_due(self):
        assert RadarService._is_due({"last_scanned_at": None}, datetime.now(timezone.utc)) is True

    def test_recent_daily_not_due(self):
        now = datetime.now(timezone.utc)
        sub = {"frequency": "daily", "last_scanned_at": (now - timedelta(hours=2)).isoformat()}
        assert RadarService._is_due(sub, now) is False

    def test_old_daily_is_due(self):
        now = datetime.now(timezone.utc)
        sub = {"frequency": "daily", "last_scanned_at": (now - timedelta(hours=21)).isoformat()}
        assert RadarService._is_due(sub, now) is True

    def test_weekly_uses_seven_day_interval(self):
        now = datetime.now(timezone.utc)
        sub = {"frequency": "weekly", "last_scanned_at": (now - timedelta(days=3)).isoformat()}
        assert RadarService._is_due(sub, now) is False


class TestCompetitorDiff:
    def test_closure_is_urgent(self):
        prev = {"name": "Rival", "business_status": "OPERATIONAL", "rating": 4.5}
        cur = {"business_status": "CLOSED_PERMANENTLY", "rating": 4.5, "review_count": 100}
        a = RadarService._diff_competitor(prev, cur)
        assert a["severity"] == "urgent" and a["category"] == "competition"
        assert "closed" in a["title"].lower()

    def test_rating_drop_is_watch(self):
        prev = {
            "name": "Rival",
            "rating": 4.6,
            "review_count": 100,
            "business_status": "OPERATIONAL",
        }
        cur = {"rating": 4.2, "review_count": 100, "business_status": "OPERATIONAL"}
        a = RadarService._diff_competitor(prev, cur)
        assert a["severity"] == "watch"
        assert "4.6" in a["title"] and "4.2" in a["title"]

    def test_review_surge_is_info(self):
        prev = {
            "name": "Rival",
            "rating": 4.5,
            "review_count": 100,
            "business_status": "OPERATIONAL",
        }
        cur = {"rating": 4.5, "review_count": 140, "business_status": "OPERATIONAL"}
        a = RadarService._diff_competitor(prev, cur)
        assert a["severity"] == "info" and "40" in a["title"]

    def test_no_material_change_returns_none(self):
        prev = {
            "name": "Rival",
            "rating": 4.5,
            "review_count": 100,
            "business_status": "OPERATIONAL",
        }
        cur = {"rating": 4.5, "review_count": 105, "business_status": "OPERATIONAL"}
        assert RadarService._diff_competitor(prev, cur) is None


class TestReputationAlert:
    def test_first_run_emits_baseline(self):
        a = RadarService._reputation_alert({}, {"rating": 4.3, "review_count": 120}, None)
        assert a["category"] == "reputation" and a["severity"] == "info"
        assert a["raw"] == {"rating": 4.3, "review_count": 120}

    def test_rating_drop_is_watch(self):
        a = RadarService._reputation_alert(
            {}, {"rating": 4.1, "review_count": 120}, {"rating": 4.4, "review_count": 120}
        )
        assert a["severity"] == "watch" and "4.4" in a["title"] and "4.1" in a["title"]

    def test_new_reviews_is_info(self):
        a = RadarService._reputation_alert(
            {}, {"rating": 4.4, "review_count": 123}, {"rating": 4.4, "review_count": 120}
        )
        assert a["severity"] == "info" and "3 new" in a["title"]

    def test_no_change_returns_none(self):
        a = RadarService._reputation_alert(
            {}, {"rating": 4.4, "review_count": 120}, {"rating": 4.4, "review_count": 120}
        )
        assert a is None


class TestCostAlert:
    def test_big_rise_is_watch(self):
        a = RadarService._cost_alert("Eggs", 3.60, 3.00, "$/doz")  # +20%
        assert a["category"] == "supply" and a["severity"] == "watch"
        assert "up 20.0%" in a["title"] and a["source"] == "fred"

    def test_small_rise_is_info(self):
        a = RadarService._cost_alert("Coffee", 6.36, 6.00, "$/lb")  # +6%
        assert a["severity"] == "info" and "up" in a["title"]

    def test_drop_is_info_with_opportunity(self):
        a = RadarService._cost_alert("Ground beef", 5.10, 6.00, "$/lb")  # -15%
        assert a["severity"] == "watch" and "down" in a["title"]
        assert "margin" in a["why_it_matters"] or "promo" in a["suggested_action"].lower()

    def test_below_threshold_returns_none(self):
        assert RadarService._cost_alert("Bread", 2.02, 2.00, "$/lb") is None  # +1%

    def test_missing_values_returns_none(self):
        assert RadarService._cost_alert("Eggs", None, 3.0, "$/doz") is None
        assert RadarService._cost_alert("Eggs", 3.0, None, "$/doz") is None
