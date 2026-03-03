from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum
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
    quantity = Column(Float, nullable=False)
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True)
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
