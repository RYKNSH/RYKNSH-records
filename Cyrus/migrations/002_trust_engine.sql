-- Cyrus Growth Engine — Trust Engine tables
-- Interaction Memory + Trust Scores

-- ---------------------------------------------------------------------------
-- Interaction Memory (Trust Engine - persistent memory)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_interaction_memory (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    entity_id uuid REFERENCES cyrus_entities(id) ON DELETE CASCADE,
    interaction_type text NOT NULL,
    channel text,
    content text,
    sentiment float DEFAULT 0,
    metadata jsonb DEFAULT '{}',
    embedding vector(1536),
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interaction_memory_entity
    ON cyrus_interaction_memory(entity_id);

CREATE INDEX IF NOT EXISTS idx_interaction_memory_embedding
    ON cyrus_interaction_memory USING ivfflat (embedding vector_cosine_ops);

ALTER TABLE cyrus_interaction_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own interactions"
    ON cyrus_interaction_memory FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Trust Scores (Trust Engine - score tracking)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_trust_scores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    entity_id uuid REFERENCES cyrus_entities(id) ON DELETE CASCADE,
    score float DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    stage text DEFAULT 'stranger' CHECK (stage IN ('stranger', 'acquaintance', 'trusted', 'partner')),
    personality_profile jsonb DEFAULT '{}',
    data_layer text DEFAULT 'l1' CHECK (data_layer IN ('l1', 'l2', 'l3')),
    last_interaction_at timestamptz,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_trust_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own trust scores"
    ON cyrus_trust_scores FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Outbound Messages (tracking sent messages)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_outbound_messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    entity_id uuid REFERENCES cyrus_entities(id) ON DELETE SET NULL,
    blueprint_id uuid REFERENCES cyrus_blueprints(id) ON DELETE CASCADE,
    channel text NOT NULL,
    personalization_level text DEFAULT 'l1',
    subject text,
    body text,
    status text DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'opened', 'replied', 'bounced')),
    sent_at timestamptz,
    opened_at timestamptz,
    replied_at timestamptz,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_outbound_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own messages"
    ON cyrus_outbound_messages FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);

-- ---------------------------------------------------------------------------
-- Inbound Magnets (tracking lead magnets)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cyrus_inbound_magnets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES cyrus_tenants(id) ON DELETE CASCADE,
    blueprint_id uuid REFERENCES cyrus_blueprints(id) ON DELETE CASCADE,
    strategy text NOT NULL,
    type text NOT NULL,
    title text NOT NULL,
    distribution_channel text,
    leads_captured int DEFAULT 0,
    is_active boolean DEFAULT true,
    metadata jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

ALTER TABLE cyrus_inbound_magnets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenants can manage own magnets"
    ON cyrus_inbound_magnets FOR ALL
    USING (auth.jwt() ->> 'tenant_id' = tenant_id::text);
