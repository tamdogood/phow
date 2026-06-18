-- Action Inbox: the owner's running to-do, auto-seeded from the Daily Brief's top actions
-- (and addable manually). Turns insight into done — the accountability/retention loop.

CREATE TABLE action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    session_id TEXT,
    user_id UUID,
    text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'daily_brief',  -- daily_brief | radar | manual
    source_id UUID,                              -- originating brief/alert id
    category TEXT,
    status TEXT NOT NULL DEFAULT 'open',          -- open | done | dismissed
    due_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_action_items_profile ON action_items(business_profile_id, status);

CREATE TRIGGER action_items_updated_at
    BEFORE UPDATE ON action_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
