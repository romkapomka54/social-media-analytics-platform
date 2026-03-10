-- Таблиця провайдерів AI
CREATE TABLE ai_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL, -- 'nvidia', 'google', 'anthropic', 'openai'
    display_name TEXT NOT NULL, -- 'NVIDIA NIM', 'Google Gemini', etc.
    base_url TEXT NOT NULL, -- API endpoint
    api_key_encrypted TEXT NOT NULL, -- зашифрований ключ (AES-256-GCM)
    is_enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100, -- чим менше число, тим вищий пріоритет
    rate_limit_rpm INTEGER DEFAULT 40, -- ліміт запитів на хвилину
    monthly_quota INTEGER, -- місячна квота в токенах
    monthly_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблиця моделей AI
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES ai_providers(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL, -- 'z-ai/glm4.7', 'gemini-2.5-flash', etc.
    display_name TEXT NOT NULL,
    context_window INTEGER NOT NULL, -- максимальна кількість токенів
    max_tokens INTEGER NOT NULL,
    supports_functions BOOLEAN DEFAULT false, -- чи підтримує виклик функцій
    supports_vision BOOLEAN DEFAULT false, -- чи підтримує зображення
    input_cost_per_1m DECIMAL(10,4) DEFAULT 0, -- ціна за 1М вхідних токенів
    output_cost_per_1m DECIMAL(10,4) DEFAULT 0,
    is_enabled BOOLEAN DEFAULT true,
    UNIQUE(provider_id, model_id)
);

-- Таблиця налаштувань клієнтів (тенантів)
CREATE TABLE tenant_ai_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL, -- 'comment_classification', 'reply_generation', 'nps_calculation'
    model_id UUID REFERENCES ai_models(id) NOT NULL,
    system_prompt TEXT, -- кастомний промпт для цієї задачі
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER,
    fallback_model_id UUID REFERENCES ai_models(id), -- модель для failover
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, task_type)
);

-- Таблиця логування використання (для білінгу)
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    task_type TEXT NOT NULL,
    provider_id UUID REFERENCES ai_providers(id),
    model_id UUID REFERENCES ai_models(id),
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    response_time_ms INTEGER,
    status TEXT DEFAULT 'success', -- success/error/failover
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Індекси для оптимізації
CREATE INDEX idx_ai_usage_tenant_date ON ai_usage_logs(tenant_id, created_at);
CREATE INDEX idx_tenant_configs_tenant ON tenant_ai_configs(tenant_id, task_type);
CREATE INDEX idx_ai_models_provider ON ai_models(provider_id);

-- Коментарі до таблиць
COMMENT ON TABLE ai_providers IS 'Зберігає API ключі та налаштування AI провайдерів';
COMMENT ON TABLE ai_models IS 'Реєстр доступних AI моделей з їх характеристиками';
COMMENT ON TABLE tenant_ai_configs IS 'Індивідуальні налаштування AI для кожного клієнта';
COMMENT ON TABLE ai_usage_logs IS 'Логування використання токенів для білінгу';
