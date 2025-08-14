-- Create outbox table for event sourcing
CREATE TABLE IF NOT EXISTS outbox (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_outbox_published_at ON outbox(published_at);
