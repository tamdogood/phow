-- Reputation Hub: connect Google Business Profile, sync reviews, draft + publish replies.
-- Single-location MVP: sentiment and the owner's response are folded into the reviews row
-- (one review -> one response) to keep the schema minimal.

CREATE TABLE review_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    platform TEXT NOT NULL DEFAULT 'google',      -- google (future: facebook, yelp)
    external_account_id TEXT,                      -- e.g. "accounts/123"
    external_location_id TEXT,                     -- e.g. "locations/456"
    location_label TEXT,                           -- human-readable location name
    access_token TEXT,                             -- Fernet-encrypted
    refresh_token TEXT,                            -- Fernet-encrypted
    token_expires_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'connected',      -- connected | disconnected | error
    last_sync_at TIMESTAMPTZ,
    last_sync_status TEXT,                          -- ok | error
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (business_profile_id, platform)
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    connection_id UUID REFERENCES review_connections ON DELETE SET NULL,
    source TEXT NOT NULL DEFAULT 'google',         -- google | manual
    external_review_id TEXT NOT NULL,
    author_name TEXT,
    author_photo_url TEXT,
    rating INT,                                     -- 1-5 normalized
    review_text TEXT,
    review_created_at TIMESTAMPTZ,
    review_url TEXT,
    -- sentiment (computed at sync time)
    sentiment TEXT,                                 -- positive | neutral | mixed | negative
    sentiment_confidence REAL,
    themes TEXT[],
    -- response lifecycle
    response_status TEXT NOT NULL DEFAULT 'needs_response',  -- needs_response | drafted | responded
    response_text TEXT,
    response_published_at TIMESTAMPTZ,
    raw_payload JSONB,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, external_review_id)
);

CREATE INDEX idx_reviews_profile_created ON reviews(business_profile_id, review_created_at DESC);
CREATE INDEX idx_reviews_profile_status ON reviews(business_profile_id, response_status);
CREATE INDEX idx_review_connections_profile ON review_connections(business_profile_id);

CREATE TRIGGER review_connections_updated_at
    BEFORE UPDATE ON review_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER reviews_updated_at
    BEFORE UPDATE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
