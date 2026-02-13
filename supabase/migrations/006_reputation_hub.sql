-- Reputation Hub core schema

CREATE TABLE review_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'disconnected',
    oauth_state TEXT,
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    connected_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (business_profile_id, source)
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    source_connection_id UUID REFERENCES review_sources(id) ON DELETE SET NULL,
    source TEXT NOT NULL,
    external_review_id TEXT NOT NULL,
    external_url TEXT,
    reviewer_name TEXT,
    rating INT NOT NULL,
    title TEXT,
    content TEXT,
    review_created_at TIMESTAMPTZ,
    reply_status TEXT NOT NULL DEFAULT 'unreplied',
    response_published_at TIMESTAMPTZ,
    raw_payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, external_review_id)
);

CREATE TABLE review_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    tone TEXT NOT NULL,
    draft_text TEXT NOT NULL,
    edited_text TEXT,
    final_text TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    idempotency_key TEXT,
    published_at TIMESTAMPTZ,
    provider_response JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE review_sentiment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL UNIQUE REFERENCES reviews(id) ON DELETE CASCADE,
    sentiment_label TEXT NOT NULL,
    sentiment_score NUMERIC(5, 4) NOT NULL,
    themes TEXT[] DEFAULT '{}',
    model_name TEXT NOT NULL DEFAULT 'heuristic-v1',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE review_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    source TEXT,
    mode TEXT NOT NULL DEFAULT 'manual',
    status TEXT NOT NULL DEFAULT 'queued',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    records_fetched INT NOT NULL DEFAULT 0,
    records_upserted INT NOT NULL DEFAULT 0,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE review_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    source TEXT,
    action TEXT NOT NULL,
    actor_session_id TEXT,
    actor_user_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE review_alert_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL UNIQUE REFERENCES business_profiles(id) ON DELETE CASCADE,
    low_rating_threshold INT NOT NULL DEFAULT 2,
    instant_low_rating_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    daily_digest_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE review_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles(id) ON DELETE CASCADE,
    review_id UUID REFERENCES reviews(id) ON DELETE SET NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query performance indexes
CREATE INDEX idx_review_sources_profile_source ON review_sources(business_profile_id, source);

CREATE INDEX idx_reviews_profile_created ON reviews(business_profile_id, review_created_at DESC);
CREATE INDEX idx_reviews_profile_status_created ON reviews(business_profile_id, reply_status, review_created_at DESC);
CREATE INDEX idx_reviews_profile_rating ON reviews(business_profile_id, rating);
CREATE INDEX idx_reviews_external ON reviews(source, external_review_id);

CREATE INDEX idx_review_responses_review ON review_responses(review_id, created_at DESC);
CREATE UNIQUE INDEX idx_review_responses_idempotency_key ON review_responses(idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX idx_review_sentiment_label ON review_sentiment(sentiment_label);

CREATE INDEX idx_review_sync_jobs_profile_created ON review_sync_jobs(business_profile_id, created_at DESC);
CREATE INDEX idx_review_sync_jobs_status ON review_sync_jobs(status);

CREATE INDEX idx_review_activity_log_profile_action ON review_activity_log(business_profile_id, action, created_at DESC);

CREATE INDEX idx_review_notifications_profile_read_created ON review_notifications(business_profile_id, is_read, created_at DESC);
CREATE INDEX idx_review_notifications_review ON review_notifications(review_id);

-- Update timestamp triggers for mutable tables
CREATE TRIGGER review_sources_updated_at
    BEFORE UPDATE ON review_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER reviews_updated_at
    BEFORE UPDATE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER review_responses_updated_at
    BEFORE UPDATE ON review_responses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER review_sentiment_updated_at
    BEFORE UPDATE ON review_sentiment
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER review_sync_jobs_updated_at
    BEFORE UPDATE ON review_sync_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER review_alert_settings_updated_at
    BEFORE UPDATE ON review_alert_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
