-- Trading Dashboard Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Paper Trading Accounts
CREATE TABLE IF NOT EXISTS paper_trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    account_name VARCHAR(255) NOT NULL,
    initial_balance DECIMAL(20, 8) NOT NULL,
    current_balance DECIMAL(20, 8) NOT NULL,
    available_balance DECIMAL(20, 8) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trades
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES paper_trading_accounts(id),
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    entry_price DECIMAL(20, 8) NOT NULL,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    quantity DECIMAL(20, 8) NOT NULL,
    entry_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    exit_price DECIMAL(20, 8),
    exit_time TIMESTAMP WITH TIME ZONE,
    profit_loss DECIMAL(20, 8),
    profit_loss_percentage DECIMAL(10, 4),
    is_open BOOLEAN DEFAULT true,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    trigger_above BOOLEAN,
    planned_rr_ratio DECIMAL(10, 2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES paper_trading_accounts(id),
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    order_type VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    filled_quantity DECIMAL(20, 8) DEFAULT 0,
    filled_price DECIMAL(20, 8),
    mode VARCHAR(10) NOT NULL DEFAULT 'paper',
    api_key_id INTEGER,
    client_order_id VARCHAR(100),
    tx_signature VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Market Data
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume_24h DECIMAL(20, 8),
    high_24h DECIMAL(20, 8),
    low_24h DECIMAL(20, 8),
    market_cap DECIMAL(20, 2),
    change_24h_percent DECIMAL(10, 4),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio Snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES paper_trading_accounts(id),
    total_value DECIMAL(20, 8) NOT NULL,
    cash_balance DECIMAL(20, 8) NOT NULL,
    invested_value DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API keys (bot authentication)
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    scopes VARCHAR(255) NOT NULL DEFAULT 'paper:write',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- Watch-only (and later hot) wallets
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    chain VARCHAR(20) NOT NULL DEFAULT 'solana',
    address VARCHAR(64) NOT NULL,
    label VARCHAR(100),
    is_watch_only BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (chain, address)
);

-- Historical OHLCV cache (backtesting)
CREATE TABLE IF NOT EXISTS ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    ts BIGINT NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    CONSTRAINT uq_ohlcv_bar UNIQUE (symbol, timeframe, ts)
);

-- Strategy registry
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    module VARCHAR(150) NOT NULL,
    params JSONB DEFAULT '{}',
    description VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Backtest runs
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
    trades JSONB,
    error VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Opt-in encrypted bot hot wallet (DISABLED by default; deny-all allowlist)
CREATE TABLE IF NOT EXISTS bot_hot_wallet (
    id SERIAL PRIMARY KEY,
    pubkey VARCHAR(64),
    encrypted_secret VARCHAR(512),
    enabled BOOLEAN NOT NULL DEFAULT false,
    max_usd_per_day DOUBLE PRECISION NOT NULL DEFAULT 10.0,
    token_allowlist JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bot_wallet_spend (
    id SERIAL PRIMARY KEY,
    day VARCHAR(10) UNIQUE NOT NULL,
    usd_spent DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

-- Indexes for better query performance
CREATE INDEX idx_trades_account_id ON trades(account_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_portfolio_snapshots_account_id ON portfolio_snapshots(account_id);
CREATE INDEX idx_portfolio_snapshots_timestamp ON portfolio_snapshots(timestamp);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE UNIQUE INDEX uq_orders_client_id ON orders(api_key_id, client_order_id)
    WHERE client_order_id IS NOT NULL;
