-- ============================================================
-- Velie Sprint 2: Multi-Tenant State
-- Supabase Migration: テナント管理 + レビュー履歴
-- ============================================================

-- 1. テナント管理テーブル
-- 各 GitHub App installation に対応する組織/ユーザー
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    installation_id BIGINT UNIQUE,          -- GitHub App installation ID
    config JSONB DEFAULT '{}'::JSONB,       -- テナント固有設定
    -- config example: {
    --   "system_prompt_override": "...",
    --   "llm_model": "claude-sonnet-4-20250514",
    --   "max_diff_chars": 60000,
    --   "review_language": "ja"
    -- }
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. レビュー履歴テーブル
-- PR ごとのレビュー結果を永続化
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE NOT NULL,
    repo_full_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    thread_id TEXT NOT NULL,                -- LangGraph thread_id (tenant:repo:pr format)
    pr_title TEXT,
    pr_author TEXT,
    review_body TEXT,
    status TEXT DEFAULT 'pending'           -- pending / completed / failed
        CHECK (status IN ('pending', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 3. インデックス
CREATE INDEX IF NOT EXISTS idx_reviews_tenant_id ON reviews(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reviews_thread_id ON reviews(thread_id);
CREATE INDEX IF NOT EXISTS idx_reviews_repo_pr ON reviews(repo_full_name, pr_number);
CREATE INDEX IF NOT EXISTS idx_tenants_installation ON tenants(installation_id);

-- 4. Row Level Security (RLS)
-- テナント分離: 各テナントは自分のデータのみアクセス可能
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_select ON reviews
    FOR SELECT USING (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

CREATE POLICY tenant_isolation_insert ON reviews
    FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

CREATE POLICY tenant_isolation_update ON reviews
    FOR UPDATE USING (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

-- 5. デフォルトテナント（RYKNSH records 本社 — 内販用）
INSERT INTO tenants (name, config)
VALUES (
    'RYKNSH records',
    '{"system_prompt_override": null, "llm_model": "claude-sonnet-4-20250514", "review_language": "ja"}'::JSONB
)
ON CONFLICT DO NOTHING;

-- 6. updated_at 自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
