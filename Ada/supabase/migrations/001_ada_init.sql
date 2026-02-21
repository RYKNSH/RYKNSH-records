-- ============================================================
-- Ada Sprint 2: Multi-Tenant State
-- Supabase Migration: テナント管理 + 使用量ログ
-- ============================================================

-- 1. テナント管理テーブル
-- APIキーベースの認証でテナントを識別
CREATE TABLE IF NOT EXISTS ada_tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    api_key TEXT UNIQUE NOT NULL,              -- Ada API key for authentication
    config JSONB DEFAULT '{}'::JSONB,          -- テナント固有設定
    -- config example: {
    --   "default_model": "claude-sonnet-4-20250514",
    --   "allowed_models": ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"],
    --   "rate_limit_rpm": 60,
    --   "monthly_budget_usd": 500.0,
    --   "system_prompt_override": null
    -- }
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 使用量ログテーブル
-- リクエストごとのトークン消費を記録（課金メーター）
CREATE TABLE IF NOT EXISTS ada_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES ada_tenants(id) ON DELETE CASCADE NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    request_id TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. インデックス
CREATE INDEX IF NOT EXISTS idx_ada_tenants_api_key ON ada_tenants(api_key);
CREATE INDEX IF NOT EXISTS idx_ada_usage_tenant ON ada_usage_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ada_usage_created ON ada_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ada_usage_tenant_created ON ada_usage_logs(tenant_id, created_at);

-- 4. Row Level Security (RLS)
ALTER TABLE ada_usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY ada_tenant_isolation_select ON ada_usage_logs
    FOR SELECT USING (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

CREATE POLICY ada_tenant_isolation_insert ON ada_usage_logs
    FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

-- Service role bypass (for server-side writes)
CREATE POLICY ada_service_role_all ON ada_usage_logs
    FOR ALL USING (current_setting('role', TRUE) = 'service_role');

-- 5. デフォルトテナント（RYKNSH records — 内販用、全子会社共通キー）
INSERT INTO ada_tenants (name, api_key, config)
VALUES (
    'RYKNSH records',
    'ada-ryknsh-internal',
    '{
        "default_model": "claude-sonnet-4-20250514",
        "allowed_models": ["claude-sonnet-4-20250514", "gpt-4o", "gpt-4o-mini"],
        "rate_limit_rpm": 120,
        "monthly_budget_usd": 1000.0
    }'::JSONB
)
ON CONFLICT (api_key) DO NOTHING;

-- 6. updated_at 自動更新トリガー
CREATE OR REPLACE FUNCTION ada_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ada_tenants_updated_at
    BEFORE UPDATE ON ada_tenants
    FOR EACH ROW EXECUTE FUNCTION ada_update_updated_at();
