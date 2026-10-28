-- Historical OHLCV cache for backtesting.
CREATE TABLE IF NOT EXISTS ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    ts BIGINT NOT NULL,                 -- bar open time, ms since epoch
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    CONSTRAINT uq_ohlcv_bar UNIQUE (symbol, timeframe, ts)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup ON ohlcv(symbol, timeframe, ts);
