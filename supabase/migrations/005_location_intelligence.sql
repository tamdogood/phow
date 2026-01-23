-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Location intelligence data (structured)
CREATE TABLE location_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    geohash TEXT NOT NULL,
    data_type TEXT NOT NULL,  -- 'crime', 'real_estate', 'permits', 'health', 'walkscore', 'trends', 'menu', 'history'
    data JSONB NOT NULL,
    source TEXT NOT NULL,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    city TEXT,
    state TEXT,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ
);

-- Vector embeddings for semantic search
CREATE TABLE data_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type TEXT NOT NULL,  -- 'crime', 'real_estate', 'permits', 'health', etc.
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI ada-002 dimension
    metadata JSONB,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    geohash TEXT,
    city TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Indexes for location_intelligence
CREATE INDEX idx_location_intel_geohash ON location_intelligence(geohash);
CREATE INDEX idx_location_intel_type ON location_intelligence(data_type);
CREATE INDEX idx_location_intel_city ON location_intelligence(city);
CREATE INDEX idx_location_intel_valid ON location_intelligence(valid_until) WHERE valid_until IS NOT NULL;

-- Indexes for data_embeddings
CREATE INDEX idx_embeddings_geohash ON data_embeddings(geohash);
CREATE INDEX idx_embeddings_source ON data_embeddings(source_type);
CREATE INDEX idx_embeddings_city ON data_embeddings(city);
CREATE INDEX idx_embeddings_expires ON data_embeddings(expires_at) WHERE expires_at IS NOT NULL;

-- Vector similarity search index (IVFFlat for approximate nearest neighbor)
CREATE INDEX idx_embeddings_vector ON data_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Health inspection scores (F&B specific)
CREATE TABLE health_inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    score INTEGER,
    grade TEXT,
    inspection_date DATE,
    violations JSONB,
    source_url TEXT,
    geohash TEXT,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_geohash ON health_inspections(geohash);
CREATE INDEX idx_health_city ON health_inspections(city);
CREATE INDEX idx_health_date ON health_inspections(inspection_date);

-- Menu/pricing data
CREATE TABLE menu_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name TEXT NOT NULL,
    business_id TEXT,  -- External ID (DoorDash, UberEats, etc.)
    platform TEXT NOT NULL,  -- 'doordash', 'ubereats', 'grubhub', 'direct'
    address TEXT,
    city TEXT NOT NULL,
    category TEXT,  -- 'coffee', 'pizza', 'burgers', etc.
    items JSONB NOT NULL,  -- [{name, price, description}]
    avg_price DECIMAL(10,2),
    price_range TEXT,  -- '$', '$$', '$$$', '$$$$'
    geohash TEXT,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_menu_geohash ON menu_data(geohash);
CREATE INDEX idx_menu_city ON menu_data(city);
CREATE INDEX idx_menu_category ON menu_data(category);
CREATE INDEX idx_menu_platform ON menu_data(platform);

-- Business history at locations
CREATE TABLE business_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    business_name TEXT NOT NULL,
    business_type TEXT,
    opened_date DATE,
    closed_date DATE,
    duration_months INTEGER,
    closure_reason TEXT,
    source TEXT,
    geohash TEXT,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_history_geohash ON business_history(geohash);
CREATE INDEX idx_history_address ON business_history(address);
CREATE INDEX idx_history_city ON business_history(city);

-- RPC function for semantic vector search
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 10,
    filter_source_types TEXT[] DEFAULT NULL,
    filter_geohash TEXT DEFAULT NULL,
    filter_city TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    source_type TEXT,
    content TEXT,
    metadata JSONB,
    location_lat DECIMAL(10,7),
    location_lng DECIMAL(10,7),
    geohash TEXT,
    city TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.source_type,
        e.content,
        e.metadata,
        e.location_lat,
        e.location_lng,
        e.geohash,
        e.city,
        1 - (e.embedding <=> query_embedding) AS similarity
    FROM data_embeddings e
    WHERE
        (filter_source_types IS NULL OR e.source_type = ANY(filter_source_types))
        AND (filter_geohash IS NULL OR e.geohash LIKE filter_geohash || '%')
        AND (filter_city IS NULL OR LOWER(e.city) LIKE '%' || LOWER(filter_city) || '%')
        AND (e.expires_at IS NULL OR e.expires_at > NOW())
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
