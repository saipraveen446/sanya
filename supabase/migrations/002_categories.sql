ALTER TABLE expenses ALTER COLUMN category TYPE VARCHAR(128);

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL UNIQUE,
    group_name VARCHAR(64) NOT NULL DEFAULT 'Daily life',
    keywords TEXT NOT NULL DEFAULT '',
    examples TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
