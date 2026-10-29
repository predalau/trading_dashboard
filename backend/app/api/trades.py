from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Trade, TradeType, PaperTradingAccount
from app.services.market_service import MarketService
from app.services.paper_accounting import (
    realized_pl,
    recompute_current_balance,
    open_paper_position,
    InsufficientBalance,
)
from app.services.pending_orders import trigger_reached, fill_pending_trade, process_pending_orders

router = APIRouter()


# Overridable in tests via app.dependency_overrides.
def get_market() -> MarketService:
    return MarketService()


class TradeCreate(BaseModel):
    symbol: str
    trade_type: str  # BUY or SELL
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: float
    notes: Optional[str] = None
    pending: bool = False              # dashboard orders set this True
    reference_price: Optional[float] = None  # current market price (to pick trigger direction)


class TradeClose(BaseModel):
    exit_price: Optional[float] = None


class TradeUpdate(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


def _serialize(t: Trade) -> dict:
    return {
        "id": t.id,
        "symbol": t.symbol,
        "trade_type": t.trade_type.value if hasattr(t.trade_type, "value") else t.trade_type,
        "entry_price": t.entry_price,
        "stop_loss": t.stop_loss,
        "take_profit": t.take_profit,
        "quantity": t.quantity,
        "exit_price": t.exit_price,
        "is_open": t.is_open,
        "status": t.status,
        "trigger_above": t.trigger_above,
        "profit_loss": t.profit_loss,
        "notes": t.notes,
        "entry_time": t.entry_time.isoformat() if t.entry_time else None,
        "exit_time": t.exit_time.isoformat() if t.exit_time else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/trades/")
async def get_trades(
    symbol: Optional[str] = None,
    open: Optional[bool] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Trade)

    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if open is not None:
        query = query.filter(Trade.is_open == open)
    if status is not None:
        query = query.filter(Trade.status == status)

    trades = query.order_by(Trade.created_at.desc()).all()
    return [_serialize(t) for t in trades]


@router.post("/trades/")
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db),
                       market: MarketService = Depends(get_market)):
    from app.services.account_service import get_or_create_default_account
    account = get_or_create_default_account(db)

    # Pending (limit/stop) order: record it resting; do NOT open or reserve margin.
    if trade.pending:
        ref = trade.reference_price
        if ref is None:
            try:
                ref = (await market.get_price(trade.symbol))["price"]
            except Exception:
                raise HTTPException(status_code=400, detail="could not determine market price for trigger")
        new_trade = Trade(
            account_id=account.id,
            symbol=trade.symbol,
            exchange="BINANCE",
            trade_type=trade.trade_type,
            entry_price=trade.entry_price,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            quantity=trade.quantity,
            notes=trade.notes,
            is_open=False,
            status="pending",
            trigger_above=trade.entry_price > ref,
        )
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        return _serialize(new_trade)

    # Immediate open (default; used by non-pending callers).
    try:
        new_trade = open_paper_position(
            db, account,
            symbol=trade.symbol, side=trade.trade_type, quantity=trade.quantity,
            price=trade.entry_price, stop_loss=trade.stop_loss,
            take_profit=trade.take_profit, notes=trade.notes,
        )
        new_trade.status = "open"
    except InsufficientBalance as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(new_trade)
    return _serialize(new_trade)


@router.post("/trades/{trade_id}/activate")
async def activate_trade(trade_id: int, db: Session = Depends(get_db),
                         market: MarketService = Depends(get_market)):
    """Open a pending order if the live price has touched its entry level.

    Authoritative: the price is fetched server-side and the trigger re-verified,
    so a client cannot force a fill at the wrong price.
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Order not found")
    if trade.status != "pending":
        raise HTTPException(status_code=409, detail=f"order is not pending (status={trade.status})")

    try:
        price = (await market.get_price(trade.symbol))["price"]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"price unavailable: {exc}")

    reached = (price >= trade.entry_price) if trade.trigger_above else (price <= trade.entry_price)
    if not reached:
        raise HTTPException(status_code=400, detail="trigger price not reached")

    result = fill_pending_trade(db, trade, price)
    db.commit()
    db.refresh(trade)
    if result == "cancelled":
        raise HTTPException(status_code=400, detail="insufficient balance at fill; order cancelled")
    return _serialize(trade)


@router.post("/trades/process-pending")
async def process_pending(db: Session = Depends(get_db),
                          market: MarketService = Depends(get_market)):
    """Check all resting pending orders against live prices and fill/cancel them.

    Called by the in-process poller (unattended) and available for manual/cron use.
    """
    return await process_pending_orders(db, market)


@router.patch("/trades/{trade_id}")
async def update_trade(trade_id: int, update: TradeUpdate, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if update.stop_loss is not None:
        trade.stop_loss = update.stop_loss
    if update.take_profit is not None:
        trade.take_profit = update.take_profit
    if update.notes is not None:
        trade.notes = update.notes

    db.commit()
    db.refresh(trade)
    return _serialize(trade)


@router.delete("/trades/{trade_id}")
async def close_trade(trade_id: int, body: Optional[TradeClose] = None, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    # Cancelling a resting pending order: no position was ever opened, no margin held.
    if trade.status == "pending":
        trade.status = "cancelled"
        trade.is_open = False
        db.commit()
        return {"message": "Order cancelled", "id": trade_id, "profit_loss": None}

    trade.is_open = False
    trade.status = "closed"
    trade.exit_time = datetime.utcnow()

    if body and body.exit_price is not None:
        trade.exit_price = body.exit_price
        trade.profit_loss, trade.profit_loss_percentage = realized_pl(
            trade.trade_type, trade.entry_price, body.exit_price, trade.quantity
        )

    # Return reserved margin to free cash, plus any realized P&L.
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == trade.account_id
    ).first()
    if account:
        account.available_balance += (trade.entry_price * trade.quantity) + (trade.profit_loss or 0.0)
        db.flush()
        recompute_current_balance(db, account)

    db.commit()
    return {"message": "Trade closed", "id": trade_id, "profit_loss": trade.profit_loss}
