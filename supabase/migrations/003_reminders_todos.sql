CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id VARCHAR(64) NOT NULL,
    title VARCHAR(200) NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    due_at TIMESTAMPTZ NOT NULL,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    notified_at TIMESTAMPTZ,
    raw_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_due_at ON reminders (due_at);
CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders (telegram_user_id);

CREATE TABLE IF NOT EXISTS todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id VARCHAR(64) NOT NULL,
    title VARCHAR(200) NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    due_at TIMESTAMPTZ,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    notified_at TIMESTAMPTZ,
    raw_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_todos_user ON todos (telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_todos_done ON todos (is_done);
CREATE INDEX IF NOT EXISTS idx_todos_due_at ON todos (due_at);
