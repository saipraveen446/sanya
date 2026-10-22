CREATE TABLE IF NOT EXISTS news_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic VARCHAR(16) NOT NULL,
    day DATE NOT NULL,
    items_json TEXT NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (topic, day)
);

CREATE INDEX IF NOT EXISTS idx_news_digests_topic_day ON news_digests (topic, day);
