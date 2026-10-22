CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id VARCHAR(64) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'INR',
    category VARCHAR(64) NOT NULL,
    merchant VARCHAR(128),
    description TEXT NOT NULL DEFAULT '',
    spent_at TIMESTAMPTZ NOT NULL,
    raw_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_spent_at ON expenses (spent_at);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category);
CREATE INDEX IF NOT EXISTS idx_expenses_telegram_user ON expenses (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_merchant ON expenses (merchant);
