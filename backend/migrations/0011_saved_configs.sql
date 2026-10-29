-- Named, reusable single-strategy backtest configurations (presets).
CREATE TABLE IF NOT EXISTS saved_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    module VARCHAR(150),
    slug VARCHAR(80),
    params JSONB,
    symbol VARCHAR(50),
    timeframe VARCHAR(10),
    lookback INTEGER,
    bias JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
