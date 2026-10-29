-- Cache of per-config backtest results so sweeps dedup repeats and can resume.
CREATE TABLE IF NOT EXISTS sweep_results (
    id SERIAL PRIMARY KEY,
    config_hash VARCHAR(64) UNIQUE NOT NULL,
    module VARCHAR(150),
    slug VARCHAR(80),
    symbol VARCHAR(50),
    timeframe VARCHAR(10),
    lookback INTEGER,
    params JSONB,
    bias JSONB,
    metrics JSONB,
    score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_sweep_results_score ON sweep_results(score DESC);
