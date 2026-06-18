-- Business Radar: per-business monitoring of news/events that could affect the business.
-- 3-tier pattern (subscription -> scans -> alerts), mirroring search_grid.

CREATE TABLE radar_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    session_id TEXT,
    user_id UUID,
    name TEXT,
    watch_topics TEXT[] NOT NULL DEFAULT '{}',
    categories TEXT[] NOT NULL DEFAULT '{competition,regulation,supply,demand,macro,local,reputation}',
    frequency TEXT NOT NULL DEFAULT 'daily',          -- daily | weekly
    schedule_hour INT NOT NULL DEFAULT 8,
    timezone TEXT DEFAULT 'America/New_York',
    status TEXT NOT NULL DEFAULT 'active',             -- active | paused
    last_scanned_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (business_profile_id)                       -- one radar per business
);

CREATE TABLE radar_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES radar_subscriptions ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'running',            -- running | completed | failed
    candidates_found INT DEFAULT 0,
    alerts_created INT DEFAULT 0,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE radar_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES radar_subscriptions ON DELETE CASCADE,
    business_profile_id UUID NOT NULL,
    scan_id UUID REFERENCES radar_scans ON DELETE SET NULL,
    title TEXT NOT NULL,
    url TEXT,
    source TEXT,            -- gdelt | places | crime | health | trends | fred
    source_domain TEXT,
    published_at TIMESTAMPTZ,
    category TEXT,          -- competition | regulation | supply | demand | macro | local | reputation
    severity TEXT,          -- info | watch | urgent
    relevance_score INT,
    summary TEXT,
    why_it_matters TEXT,
    suggested_action TEXT,
    status TEXT NOT NULL DEFAULT 'new',   -- new | read | dismissed
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_radar_subs_profile ON radar_subscriptions(business_profile_id);
CREATE INDEX idx_radar_subs_status ON radar_subscriptions(status);
CREATE INDEX idx_radar_scans_sub ON radar_scans(subscription_id);
CREATE INDEX idx_radar_alerts_profile ON radar_alerts(business_profile_id, status);
CREATE INDEX idx_radar_alerts_sub ON radar_alerts(subscription_id);
CREATE INDEX idx_radar_alerts_created ON radar_alerts(created_at DESC);

CREATE TRIGGER radar_subscriptions_updated_at
    BEFORE UPDATE ON radar_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
