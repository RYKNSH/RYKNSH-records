-- Cyrus Sprint 6: PLG Launch — Tenants & API Keys
-- Run after 001_initial.sql and 002_trust_engine.sql

-- Tenants table
CREATE TABLE IF NOT EXISTS cyrus_tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'usage', 'growth', 'full_outcome')),
    settings JSONB DEFAULT '{}',
    monthly_run_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE IF NOT EXISTS cyrus_api_keys (
    key_hash TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES cyrus_tenants(tenant_id) ON DELETE CASCADE,
    name TEXT DEFAULT 'default',
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blueprint storage
CREATE TABLE IF NOT EXISTS cyrus_blueprints (
    blueprint_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES cyrus_tenants(tenant_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    business_model TEXT NOT NULL CHECK (business_model IN ('b2b', 'b2c', 'c2c')),
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pipeline execution log
CREATE TABLE IF NOT EXISTS cyrus_pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES cyrus_tenants(tenant_id),
    blueprint_id TEXT REFERENCES cyrus_blueprints(blueprint_id),
    pipeline_type TEXT NOT NULL CHECK (pipeline_type IN ('intelligence', 'growth')),
    conversion_mode TEXT CHECK (conversion_mode IN ('b2b', 'b2c', 'c2c')),
    node_count INTEGER,
    duration_ms FLOAT,
    status TEXT DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed')),
    result JSONB DEFAULT '{}',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Outcome tracking (for Full Outcome pricing)
CREATE TABLE IF NOT EXISTS cyrus_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL REFERENCES cyrus_tenants(tenant_id),
    run_id UUID REFERENCES cyrus_pipeline_runs(run_id),
    metric TEXT NOT NULL,
    value FLOAT NOT NULL,
    revenue_attributed FLOAT DEFAULT 0,
    cyrus_fee FLOAT DEFAULT 0,
    fee_rate FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON cyrus_api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_tenant ON cyrus_blueprints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_tenant ON cyrus_pipeline_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_created ON cyrus_pipeline_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_outcomes_tenant ON cyrus_outcomes(tenant_id);

-- RLS
ALTER TABLE cyrus_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE cyrus_api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE cyrus_blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE cyrus_pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE cyrus_outcomes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation: tenants" ON cyrus_tenants
    FOR ALL USING (tenant_id = current_setting('app.tenant_id', TRUE));
CREATE POLICY "Tenant isolation: api_keys" ON cyrus_api_keys
    FOR ALL USING (tenant_id = current_setting('app.tenant_id', TRUE));
CREATE POLICY "Tenant isolation: blueprints" ON cyrus_blueprints
    FOR ALL USING (tenant_id = current_setting('app.tenant_id', TRUE));
CREATE POLICY "Tenant isolation: runs" ON cyrus_pipeline_runs
    FOR ALL USING (tenant_id = current_setting('app.tenant_id', TRUE));
CREATE POLICY "Tenant isolation: outcomes" ON cyrus_outcomes
    FOR ALL USING (tenant_id = current_setting('app.tenant_id', TRUE));
