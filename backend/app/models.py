from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, JSON, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
from enum import Enum
from datetime import datetime


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PaperTradingAccount(Base):
    __tablename__ = "paper_trading_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    initial_balance = Column(Float, nullable=False)
    current_balance = Column(Float, nullable=False)
    available_balance = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)  # e.g., BTC/USDT, SOL/USDC
    exchange = Column(String(50), nullable=False)  # e.g., BINANCE, SOLANA
    trade_type = Column(SQLEnum(TradeType), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True)
    status = Column(String(20), nullable=False, default="open")  # pending | open | closed | cancelled
    trigger_above = Column(Boolean, nullable=True)  # pending entry fills when price >= entry (True) / <= entry (False)
    planned_rr_ratio = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    order_type = Column(String(50), nullable=False)  # LIMIT, MARKET, STOP_LOSS, etc.
    side = Column(SQLEnum(TradeType), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    filled_quantity = Column(Float, default=0)
    filled_price = Column(Float, nullable=True)
    mode = Column(String(10), nullable=False, default="paper")  # paper | solana
    api_key_id = Column(Integer, nullable=True, index=True)      # bot that placed it
    client_order_id = Column(String(100), nullable=True)         # idempotency key
    tx_signature = Column(String(128), nullable=True)            # solana settlement
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    high_24h = Column(Float, nullable=True)
    low_24h = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    change_24h_percent = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False)
    key_prefix = Column(String(16), nullable=False)       # shown in UI, e.g. 'ith_ab12cd'
    key_hash = Column(String(128), nullable=False, index=True)  # sha256 of full key
    scopes = Column(String(255), nullable=False, default="paper:write")  # CSV
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    chain = Column(String(20), nullable=False, default="solana")
    address = Column(String(64), nullable=False)
    label = Column(String(100), nullable=True)
    is_watch_only = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OHLCV(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    ts = Column(BigInteger, nullable=False, index=True)  # bar open time, ms since epoch
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("symbol", "timeframe", "ts", name="uq_ohlcv_bar"),)


class StrategyDef(Base):
    """A registered trading strategy (Python module in backend/strategies/)."""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    module = Column(String(150), nullable=False)  # e.g. strategies.sma_cross
    params = Column(JSON, default=dict)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, nullable=True, index=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_ts = Column(BigInteger, nullable=True)
    end_ts = Column(BigInteger, nullable=True)
    params = Column(JSON, default=dict)
    status = Column(String(20), default="pending")  # pending | done | error
    metrics = Column(JSON, nullable=True)
    equity_curve = Column(JSON, nullable=True)
    trades = Column(JSON, nullable=True)
    error = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Sweep(Base):
    """A parameter-sweep (grid-search) job over backtest settings."""
    __tablename__ = "sweeps"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default="running")  # running | done | error
    total = Column(Integer, default=0)
    done = Column(Integer, default=0)
    score_metric = Column(String(30), default="total_return")
    lookback = Column(Integer, default=1000)
    results = Column(JSON, nullable=True)   # top-N [{config, metrics, score}]
    error = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SweepResult(Base):
    """Cached backtest result for one config (dedup + resume across sweeps)."""
    __tablename__ = "sweep_results"

    id = Column(Integer, primary_key=True, index=True)
    config_hash = Column(String(64), unique=True, index=True, nullable=False)
    module = Column(String(150))
    slug = Column(String(80))
    symbol = Column(String(50))
    timeframe = Column(String(10))
    lookback = Column(Integer)
    params = Column(JSON)
    bias = Column(JSON)
    metrics = Column(JSON)
    score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BotHotWallet(Base):
    """Opt-in encrypted hot wallet for unattended bots. DISABLED by default.

    Guardrails (enforced in hotwallet_service): enabled flag, per-day USD cap,
    and a token allowlist that starts EMPTY = deny-all.
    """
    __tablename__ = "bot_hot_wallet"

    id = Column(Integer, primary_key=True, index=True)
    pubkey = Column(String(64), nullable=True)
    encrypted_secret = Column(String(512), nullable=True)   # Fernet ciphertext of the secret key
    enabled = Column(Boolean, nullable=False, default=False)
    max_usd_per_day = Column(Float, nullable=False, default=10.0)
    token_allowlist = Column(JSON, default=list)            # [] => deny-all
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BotWalletSpend(Base):
    __tablename__ = "bot_wallet_spend"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD (UTC)
    usd_spent = Column(Float, nullable=False, default=0.0)
