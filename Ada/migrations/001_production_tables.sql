-- Ada Core API — Supabase Table Definitions
-- Run this migration to create all tables needed for production.

-- API Keys (hashed, never store plain text)
CREATE TABLE IF NOT EXISTS ada_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name TEXT DEFAULT 'default',
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON ada_api_keys(key_hash) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON ada_api_keys(tenant_id);

-- Subscriptions (billing state)
CREATE TABLE IF NOT EXISTS ada_subscriptions (
    tenant_id UUID PRIMARY KEY,
    plan TEXT DEFAULT 'free',
    stripe_customer_id TEXT DEFAULT '',
    stripe_subscription_id TEXT DEFAULT '',
    request_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenants
CREATE TABLE IF NOT EXISTS ada_tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    company_name TEXT DEFAULT '',
    name TEXT DEFAULT '',
    plan TEXT DEFAULT 'free',
    api_key TEXT DEFAULT '',  -- legacy, kept for backward compat
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_email ON ada_tenants(email);
CREATE INDEX IF NOT EXISTS idx_tenants_api_key ON ada_tenants(api_key) WHERE api_key != '';

-- Blueprints
CREATE TABLE IF NOT EXISTS ada_blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    version INTEGER DEFAULT 1,
    name TEXT DEFAULT 'default',
    persona TEXT DEFAULT '',
    system_prompt TEXT DEFAULT '',
    priority_weights JSONB DEFAULT '{}',
    allowed_models JSONB DEFAULT '[]',
    default_model TEXT DEFAULT 'claude-sonnet-4-20250514',
    temperature FLOAT DEFAULT 0.7,
    tools JSONB DEFAULT '[]',
    quality_tier TEXT DEFAULT 'standard',
    rag_enabled BOOLEAN DEFAULT TRUE,
    max_retries INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blueprints_tenant ON ada_blueprints(tenant_id);

-- Feedback
CREATE TABLE IF NOT EXISTS ada_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    request_id TEXT DEFAULT '',
    model TEXT DEFAULT '',
    rating INTEGER,
    validation_score FLOAT DEFAULT 0.0,
    grounding_score FLOAT DEFAULT 0.0,
    was_retried BOOLEAN DEFAULT FALSE,
    response_edited BOOLEAN DEFAULT FALSE,
    overall_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_tenant ON ada_feedback(tenant_id);

-- RLS Policies (anon key read/write for now, tighten later)
ALTER TABLE ada_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE ada_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ada_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ada_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE ada_feedback ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "service_all_api_keys" ON ada_api_keys FOR ALL USING (TRUE);
CREATE POLICY "service_all_subscriptions" ON ada_subscriptions FOR ALL USING (TRUE);
CREATE POLICY "service_all_tenants" ON ada_tenants FOR ALL USING (TRUE);
CREATE POLICY "service_all_blueprints" ON ada_blueprints FOR ALL USING (TRUE);
CREATE POLICY "service_all_feedback" ON ada_feedback FOR ALL USING (TRUE);
