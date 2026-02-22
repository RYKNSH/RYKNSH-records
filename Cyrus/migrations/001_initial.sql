-- Cyrus Growth Engine — Initial Schema
-- Tenant, Blueprint, Entity, Signal, Campaign tables with RLS

-- Enable pgvector (for future embedding use)
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Tenants
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    api_key text UNIQUE NOT NULL,
    settings jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_tenants ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can view themselves"
    ON cyrus_tenants FOR SELECT
    USING (auth.jwt() ->> 'tenant_id' = id::text);

-- ---------------------------------------------------------------------------
-- Blueprints
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_blueprints (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    name text NOT NULL DEFAULT '',
    business_model text NOT NULL CHECK (business_model IN ('b2b', 'b2c', 'c2c')),
    deal_complexity text DEFAULT 'standard' CHECK (deal_complexity IN ('low', 'standard', 'high')),
    entity_config jsonb NOT NULL DEFAULT '{}',
    trust_config jsonb DEFAULT '{}',
    acquisition_config jsonb DEFAULT '{}',
    conversion_config jsonb DEFAULT '{}',
    pricing_model text DEFAULT 'growth',
    outcome_config jsonb DEFAULT NULL,
    version int DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_blueprints ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own blueprints"
    ON cyrus_blueprints FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Entities
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    entity_type text NOT NULL CHECK (entity_type IN ('organization', 'individual', 'creator')),
    data jsonb NOT NULL DEFAULT '{}',
    trust_score float DEFAULT 0,
    personalization_level text DEFAULT 'l1_surface',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_entities ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own entities"
    ON cyrus_entities FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Signals
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_signals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    entity_id uuid REFERENCES cyrus_entities(id) ON DELETE SET NULL,
    signal_type text NOT NULL,
    source text NOT NULL,
    confidence float DEFAULT 0,
    priority text DEFAULT 'medium',
    metadata jsonb DEFAULT '{}',
    detected_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own signals"
    ON cyrus_signals FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Campaigns
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_campaigns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    blueprint_id uuid REFERENCES cyrus_blueprints(id) ON DELETE CASCADE,
    business_model text NOT NULL CHECK (business_model IN ('b2b', 'b2c', 'c2c')),
    name text DEFAULT '',
    channel text,
    status text DEFAULT 'draft',
    metrics jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_campaigns ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own campaigns"
    ON cyrus_campaigns FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Intelligence Results (cached)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_intelligence_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    blueprint_id uuid REFERENCES cyrus_blueprints(id) ON DELETE CASCADE,
    market_data jsonb DEFAULT '{}',
    icp_profiles jsonb DEFAULT '[]',
    detected_signals jsonb DEFAULT '[]',
    node_metrics jsonb DEFAULT '[]',
    created_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_intelligence_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can view own intelligence results"
    ON cyrus_intelligence_results FOR SELECT
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);
