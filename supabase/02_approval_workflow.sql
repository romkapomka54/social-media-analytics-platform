-- Таблиця для чернеток відповідей
CREATE TABLE draft_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    comment_id TEXT NOT NULL,
    comment_text TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'instagram', 'youtube', 'tiktok'
    platform_comment_id TEXT,
    platform_post_id TEXT,
    ai_generated_reply TEXT NOT NULL,
    original_sentiment_score INTEGER,
    original_nps_category TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'published'
    reviewed_by UUID REFERENCES tenants(id),
    reviewed_at TIMESTAMP,
    published_at TIMESTAMP,
    published_comment_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблиця для логування workflow
CREATE TABLE approval_workflow_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID REFERENCES draft_responses(id) ON DELETE CASCADE,
    action TEXT NOT NULL, -- 'created', 'approved', 'rejected', 'published'
    performed_by UUID REFERENCES tenants(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Індекси
CREATE INDEX idx_drafts_tenant_status ON draft_responses(tenant_id, status);
CREATE INDEX idx_drafts_platform_comment ON draft_responses(platform, platform_comment_id);
CREATE INDEX idx_workflow_logs_draft ON approval_workflow_logs(draft_id);

-- Коментарі
COMMENT ON TABLE draft_responses IS 'Чернетки відповідей, згенеровані ШІ, які очікують на схвалення';
COMMENT ON TABLE approval_workflow_logs IS 'Лог дій Approval Workflow (створення, схвалення, відхилення, публікація)';
