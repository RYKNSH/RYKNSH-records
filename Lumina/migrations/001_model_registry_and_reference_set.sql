-- Supabase Migration: Lumina Model Registry + Reference Set
-- pgvector extension required

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Model Registry
CREATE TABLE IF NOT EXISTS lumina_model_registry (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL DEFAULT 'image',
    provider TEXT NOT NULL,
    api_endpoint TEXT DEFAULT '',
    capability_score FLOAT DEFAULT 0.0,
    cost_per_call FLOAT DEFAULT 0.0,
    strengths JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reference Set (pgvector)
CREATE TABLE IF NOT EXISTS lumina_reference_set (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    image_url TEXT NOT NULL,
    description TEXT DEFAULT '',
    embedding VECTOR(1536),
    tags TEXT[] DEFAULT '{}',
    score FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_model_registry_active
    ON lumina_model_registry (is_active, model_type);

CREATE INDEX IF NOT EXISTS idx_reference_set_tenant
    ON lumina_reference_set (tenant_id);

CREATE INDEX IF NOT EXISTS idx_reference_set_embedding
    ON lumina_reference_set
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- pgvector similarity search function
CREATE OR REPLACE FUNCTION match_reference_images(
    query_embedding VECTOR(1536),
    match_threshold FLOAT,
    match_count INT,
    p_tenant_id TEXT DEFAULT 'default'
)
RETURNS TABLE (
    id UUID,
    tenant_id TEXT,
    image_url TEXT,
    description TEXT,
    tags TEXT[],
    score FLOAT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.tenant_id,
        r.image_url,
        r.description,
        r.tags,
        r.score,
        1 - (r.embedding <=> query_embedding) AS similarity
    FROM lumina_reference_set r
    WHERE r.tenant_id = p_tenant_id
        AND 1 - (r.embedding <=> query_embedding) > match_threshold
    ORDER BY r.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Seed data: Model Registry
INSERT INTO lumina_model_registry (id, model_name, model_type, provider, capability_score, cost_per_call, strengths)
VALUES
    ('flux-1.1-pro', 'Flux 1.1 Pro', 'image', 'black-forest-labs', 92, 0.04, '{"composition": 0.9, "photorealism": 0.85, "artistic": 0.8, "text_rendering": 0.6}'),
    ('dall-e-3', 'DALL-E 3', 'image', 'openai', 85, 0.04, '{"composition": 0.8, "text_rendering": 0.9, "photorealism": 0.7, "artistic": 0.75}'),
    ('sd-xl-turbo', 'Stable Diffusion XL Turbo', 'image', 'stability-ai', 78, 0.01, '{"composition": 0.7, "artistic": 0.85, "photorealism": 0.6, "text_rendering": 0.3}')
ON CONFLICT (id) DO NOTHING;

-- RLS Policies
ALTER TABLE lumina_model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE lumina_reference_set ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON lumina_model_registry
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON lumina_reference_set
    FOR ALL USING (auth.role() = 'service_role');
