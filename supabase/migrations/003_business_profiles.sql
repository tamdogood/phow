-- Business Profiles: Core entity for all tools to share context
CREATE TABLE business_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    user_id UUID,  -- Optional, for future auth
    business_name TEXT,
    business_type TEXT NOT NULL,  -- 'coffee_shop', 'restaurant', 'retail', etc.
    business_description TEXT,
    target_customers TEXT,  -- Description of ideal customer
    location_address TEXT,
    location_lat DECIMAL(10, 7),
    location_lng DECIMAL(10, 7),
    location_place_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tracked Competitors: Competitors identified and tracked for a business
CREATE TABLE tracked_competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID REFERENCES business_profiles ON DELETE CASCADE,
    place_id TEXT NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    lat DECIMAL(10, 7),
    lng DECIMAL(10, 7),
    rating DECIMAL(2, 1),
    review_count INT,
    price_level INT,  -- 1-4 scale
    business_status TEXT,  -- 'OPERATIONAL', 'CLOSED_TEMPORARILY', etc.
    categories TEXT[],  -- Array of business categories
    strengths TEXT[],  -- Extracted from review analysis
    weaknesses TEXT[],  -- Extracted from review analysis
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_profile_id, place_id)
);

-- Market Analysis Results: Cached market validation data
CREATE TABLE market_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID REFERENCES business_profiles ON DELETE CASCADE,
    viability_score INT,  -- 1-100
    demographics JSONB,  -- Age, income, education breakdown
    demand_indicators JSONB,  -- Search trends, foot traffic
    competition_saturation JSONB,  -- Competitor density analysis
    market_size_estimates JSONB,  -- TAM, SAM, SOM
    risk_factors JSONB,  -- List of identified risks
    opportunities JSONB,  -- List of identified opportunities
    recommendations TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Competitor Analyses: Deep competitor analysis results
CREATE TABLE competitor_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID REFERENCES business_profiles ON DELETE CASCADE,
    overall_competition_level TEXT,  -- 'low', 'moderate', 'high', 'saturated'
    positioning_data JSONB,  -- Price vs quality positioning
    market_gaps JSONB,  -- Identified gaps/opportunities
    sentiment_summary JSONB,  -- Aggregated sentiment across competitors
    pricing_insights JSONB,  -- Price range, average, distribution
    differentiation_suggestions TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX idx_business_profiles_session ON business_profiles(session_id);
CREATE INDEX idx_business_profiles_type ON business_profiles(business_type);
CREATE INDEX idx_tracked_competitors_profile ON tracked_competitors(business_profile_id);
CREATE INDEX idx_market_analyses_profile ON market_analyses(business_profile_id);
CREATE INDEX idx_competitor_analyses_profile ON competitor_analyses(business_profile_id);

-- Update timestamp trigger for business_profiles
CREATE TRIGGER business_profiles_updated_at
    BEFORE UPDATE ON business_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
