-- Strategy registry + backtest runs.
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    module VARCHAR(150) NOT NULL,
    params JSONB DEFAULT '{}',
    description VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_ts BIGINT,
    end_ts BIGINT,
    params JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    metrics JSONB,
    equity_curve JSONB,
    error VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_backtests_strategy ON backtests(strategy_id);
