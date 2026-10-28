-- Watch-only (and later hot) wallets for asset tracking.
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    chain VARCHAR(20) NOT NULL DEFAULT 'solana',
    address VARCHAR(64) NOT NULL,
    label VARCHAR(100),
    is_watch_only BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (chain, address)
);
