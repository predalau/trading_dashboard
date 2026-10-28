-- Opt-in encrypted bot hot wallet (DISABLED by default; deny-all allowlist).
CREATE TABLE IF NOT EXISTS bot_hot_wallet (
    id SERIAL PRIMARY KEY,
    pubkey VARCHAR(64),
    encrypted_secret VARCHAR(512),
    enabled BOOLEAN NOT NULL DEFAULT false,
    max_usd_per_day DOUBLE PRECISION NOT NULL DEFAULT 10.0,
    token_allowlist JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bot_wallet_spend (
    id SERIAL PRIMARY KEY,
    day VARCHAR(10) UNIQUE NOT NULL,
    usd_spent DOUBLE PRECISION NOT NULL DEFAULT 0.0
);
