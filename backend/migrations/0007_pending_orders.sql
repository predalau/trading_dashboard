-- Pending (limit/stop) entry orders: a trade stays pending until price touches
-- the entry level, then it opens. trigger_above = fill when price >= entry.
ALTER TABLE trades ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'open';
ALTER TABLE trades ADD COLUMN IF NOT EXISTS trigger_above BOOLEAN;
UPDATE trades SET status = CASE WHEN is_open THEN 'open' ELSE 'closed' END;
