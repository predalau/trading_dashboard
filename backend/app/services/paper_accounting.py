"""Paper-trading accounting: P&L, balance recomputation, and opening positions.

Shared by the dashboard trade endpoint (app.api.trades) and the paper
execution venue (app.execution.paper) so the balance math lives in one place.
"""
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import PaperTradingAccount, Trade


class InsufficientBalance(Exception):
    """Raised when an open would cost more than the account's available cash."""


def realized_pl(trade_type, entry: float, exit_price: float, quantity: float):
    """Return (pl, pl_pct) for a closed trade.

    LONG (BUY) profits when price rises; SHORT (SELL) profits when price falls.
    """
    tt = trade_type.value if hasattr(trade_type, "value") else str(trade_type)
    direction = 1 if tt.upper() == "BUY" else -1
    pl = direction * (exit_price - entry) * quantity
    pct = (pl / (entry * quantity) * 100) if entry and quantity else 0.0
    return pl, pct


def recompute_current_balance(db: Session, account: PaperTradingAccount) -> None:
    """current_balance = free cash + margin reserved by still-open positions.

    Opening a position moves notional from available into reserved (equity flat);
    closing returns the margin +/- realized P&L (equity changes by P&L).
    """
    reserved = db.query(
        func.coalesce(func.sum(Trade.entry_price * Trade.quantity), 0.0)
    ).filter(Trade.account_id == account.id, Trade.is_open.is_(True)).scalar() or 0.0
    account.current_balance = account.available_balance + reserved


def open_paper_position(
    db: Session,
    account: PaperTradingAccount,
    *,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    notes: Optional[str] = None,
    exchange: str = "BINANCE",
) -> Trade:
    """Reserve margin and create an open Trade. Raises InsufficientBalance.

    The caller is responsible for commit(); this only flushes so the new row
    participates in the reserved-margin recomputation.
    """
    cost = price * quantity
    if cost > account.available_balance:
        raise InsufficientBalance("Insufficient balance for this trade")
    trade = Trade(
        account_id=account.id,
        symbol=symbol,
        exchange=exchange,
        trade_type=side,
        entry_price=price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        quantity=quantity,
        notes=notes,
        is_open=True,
    )
    account.available_balance -= cost
    db.add(trade)
    db.flush()
    recompute_current_balance(db, account)
    return trade
