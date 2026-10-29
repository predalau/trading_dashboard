-- Parameter-sweep (grid-search) jobs over backtest settings.
CREATE TABLE IF NOT EXISTS sweeps (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'running',
    total INTEGER DEFAULT 0,
    done INTEGER DEFAULT 0,
    score_metric VARCHAR(30) DEFAULT 'total_return',
    lookback INTEGER DEFAULT 1000,
    results JSONB,
    error VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
