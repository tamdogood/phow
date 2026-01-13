-- LLM Responses: Track all LLM calls and responses
CREATE TABLE llm_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations ON DELETE CASCADE,
    message_id UUID REFERENCES messages ON DELETE SET NULL,
    provider TEXT NOT NULL,  -- 'openai' or 'anthropic'
    model TEXT NOT NULL,  -- 'gpt-4o', 'claude-sonnet-4-20250514', etc.
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    latency_ms INT,  -- Response time in milliseconds
    input_messages JSONB,  -- The messages sent to the LLM
    output_content TEXT,  -- The LLM's response
    metadata JSONB,  -- Additional metadata (temperature, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tool Activities: Track all tool invocations
CREATE TABLE tool_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,  -- 'location_scout', etc.
    tool_name TEXT NOT NULL,  -- 'discover_neighborhood', 'geocode_address', etc.
    status TEXT NOT NULL DEFAULT 'started',  -- 'started', 'completed', 'failed'
    input_args JSONB,  -- Arguments passed to the tool
    output_data JSONB,  -- Tool response data
    error_message TEXT,  -- Error message if failed
    latency_ms INT,  -- Execution time in milliseconds
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes for efficient queries
CREATE INDEX idx_llm_responses_conversation ON llm_responses(conversation_id);
CREATE INDEX idx_llm_responses_provider ON llm_responses(provider);
CREATE INDEX idx_llm_responses_created ON llm_responses(created_at);

CREATE INDEX idx_tool_activities_conversation ON tool_activities(conversation_id);
CREATE INDEX idx_tool_activities_session ON tool_activities(session_id);
CREATE INDEX idx_tool_activities_tool ON tool_activities(tool_id, tool_name);
CREATE INDEX idx_tool_activities_status ON tool_activities(status);
CREATE INDEX idx_tool_activities_started ON tool_activities(started_at);
