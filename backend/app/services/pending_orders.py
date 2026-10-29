"""Pending (limit/stop) order triggering — shared by the /activate endpoint and
the background poller so the fill logic lives in one place.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import PaperTradingAccount, Trade
from app.services.paper_accounting import recompute_current_balance


def trigger_reached(trade: Trade, price: float) -> bool:
    """True once the market price has touched the order's entry level."""
    if trade.trigger_above:
        return price >= trade.entry_price
    return price <= trade.entry_price


def fill_pending_trade(db: Session, trade: Trade, price: float) -> str:
    """Open a pending trade at its entry price (reserving margin).

    Returns 'open' on success, or 'cancelled' if the account can't cover it.
    Caller is responsible for commit().
    """
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == trade.account_id
    ).first()
    cost = trade.entry_price * trade.quantity
    if not account or cost > account.available_balance:
        trade.status = "cancelled"
        return "cancelled"
    account.available_balance -= cost
    trade.is_open = True
    trade.status = "open"
    trade.entry_time = datetime.utcnow()
    db.flush()
    recompute_current_balance(db, account)
    return "open"


async def process_pending_orders(db: Session, market) -> dict:
    """Check every pending order against the live price; fill/cancel as needed.

    One price fetch per distinct symbol. `market` is a MarketService.
    """
    pending = db.query(Trade).filter(Trade.status == "pending").all()
    if not pending:
        return {"checked": 0, "filled": [], "cancelled": []}

    prices: dict[str, float | None] = {}
    filled, cancelled = [], []
    for trade in pending:
        if trade.symbol not in prices:
            try:
                prices[trade.symbol] = (await market.get_price(trade.symbol))["price"]
            except Exception:
                prices[trade.symbol] = None
        price = prices[trade.symbol]
        if price is None:
            continue
        if trigger_reached(trade, price):
            result = fill_pending_trade(db, trade, price)
            (filled if result == "open" else cancelled).append(trade.id)

    db.commit()
    return {"checked": len(pending), "filled": filled, "cancelled": cancelled}
