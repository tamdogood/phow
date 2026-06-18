-- Feasibility Reports: complete, deterministic food & drink feasibility studies.
-- One JSONB-row artifact per study; job status lives on the row (single-shot pipeline).
CREATE TABLE feasibility_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id UUID,                                              -- optional (future auth)
    business_profile_id UUID REFERENCES business_profiles ON DELETE SET NULL,  -- optional

    -- structured inputs
    concept TEXT NOT NULL,                                     -- F&B type/cuisine, e.g. "specialty coffee shop"
    location_address TEXT NOT NULL,
    location_lat DECIMAL(10, 7),
    location_lng DECIMAL(10, 7),
    naics_code TEXT,
    scale_seats INT,
    startup_budget INT,

    -- job lifecycle
    status TEXT NOT NULL DEFAULT 'pending',                    -- pending | running | completed | failed
    progress JSONB,                                            -- {step, steps_total, label, completed[]}
    error TEXT,

    -- synthesized headline (denormalized for list views)
    verdict TEXT,                                              -- GO | GO_WITH_CONDITIONS | NO_GO
    viability_score INT,
    title TEXT,

    -- the full FeasibilityReport artifact
    report JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_feasibility_session ON feasibility_reports(session_id);
CREATE INDEX idx_feasibility_user ON feasibility_reports(user_id);
CREATE INDEX idx_feasibility_profile ON feasibility_reports(business_profile_id);

CREATE TRIGGER feasibility_reports_updated_at
    BEFORE UPDATE ON feasibility_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
