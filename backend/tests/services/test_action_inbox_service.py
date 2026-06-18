"""Tests for ActionInboxService pure logic: dedupe-on-seed + row building."""

from app.services.action_inbox_service import ActionInboxService


class TestNewActions:
    def test_skips_existing_open_case_insensitive(self):
        existing = ["Reply to reviews"]
        actions = ["reply to reviews", "Check competitor", "Run a promo"]
        assert ActionInboxService._new_actions(existing, actions) == [
            "Check competitor",
            "Run a promo",
        ]

    def test_dedupes_within_batch_and_strips(self):
        out = ActionInboxService._new_actions([], ["  Do X  ", "do x", "Do Y"])
        assert out == ["Do X", "Do Y"]

    def test_skips_blanks(self):
        assert ActionInboxService._new_actions([], ["", "   ", "Real"]) == ["Real"]


class TestRow:
    def test_brief_row_carries_source_and_ids(self):
        row = ActionInboxService._row(
            "bp1", "Reply today", source="daily_brief", source_id="brief1", user_id="u1"
        )
        assert row["business_profile_id"] == "bp1"
        assert row["text"] == "Reply today"
        assert row["source"] == "daily_brief"
        assert row["source_id"] == "brief1"
        assert row["user_id"] == "u1"
        assert row["status"] == "open"
        assert "id" in row
        assert "session_id" not in row  # omitted when falsy

    def test_manual_row_truncates_long_text(self):
        row = ActionInboxService._row("bp1", "x" * 600, source="manual")
        assert len(row["text"]) == 500
        assert row["source"] == "manual"
