-- Bot API: api_keys table + order execution/audit columns.

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    scopes VARCHAR(255) NOT NULL DEFAULT 'paper:write',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_used_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);

ALTER TABLE orders ADD COLUMN IF NOT EXISTS mode VARCHAR(10) NOT NULL DEFAULT 'paper';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS api_key_id INTEGER REFERENCES api_keys(id);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS client_order_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tx_signature VARCHAR(128);

-- Idempotency: one (api_key_id, client_order_id) pair maps to one order.
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_client_id
    ON orders(api_key_id, client_order_id)
    WHERE client_order_id IS NOT NULL;
