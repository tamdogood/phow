-- Daily Brief: one AI-synthesized morning briefing per business per day.
-- Distills the day's radar alerts (news + competitor moves + reputation) into a
-- pulse, a narrative, prioritized highlights, and the top 1-3 actions to take today.

CREATE TABLE daily_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    session_id TEXT,
    user_id UUID,
    brief_date DATE NOT NULL DEFAULT CURRENT_DATE,
    pulse TEXT NOT NULL DEFAULT 'calm',        -- calm | watch | alert
    headline TEXT,
    narrative TEXT,
    highlights JSONB NOT NULL DEFAULT '[]',    -- [{title, category, severity, why_it_matters, suggested_action, url, alert_id}]
    top_actions JSONB NOT NULL DEFAULT '[]',   -- ["...", "..."]
    stats JSONB NOT NULL DEFAULT '{}',         -- {alerts_total, urgent, watch, competitor_moves, new_reviews}
    alert_ids JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (business_profile_id, brief_date)   -- one brief per business per day
);

CREATE INDEX idx_daily_briefs_profile ON daily_briefs(business_profile_id, brief_date DESC);

CREATE TRIGGER daily_briefs_updated_at
    BEFORE UPDATE ON daily_briefs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
