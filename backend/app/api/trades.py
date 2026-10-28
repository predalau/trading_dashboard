from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import Trade, TradeType, PaperTradingAccount
from app.services.paper_accounting import (
    realized_pl,
    recompute_current_balance,
    open_paper_position,
    InsufficientBalance,
)

router = APIRouter()




class TradeCreate(BaseModel):
    symbol: str
    trade_type: str  # BUY or SELL
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: float
    notes: Optional[str] = None


class TradeClose(BaseModel):
    exit_price: Optional[float] = None


class TradeUpdate(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    symbol: str
    trade_type: str
    entry_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    quantity: float
    exit_price: Optional[float]
    is_open: bool
    notes: Optional[str]
    entry_time: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/trades/")
async def get_trades(
    symbol: Optional[str] = None,
    open: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Trade)

    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if open is not None:
        query = query.filter(Trade.is_open == open)

    trades = query.order_by(Trade.created_at.desc()).all()

    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "trade_type": t.trade_type.value if hasattr(t.trade_type, 'value') else t.trade_type,
            "entry_price": t.entry_price,
            "stop_loss": t.stop_loss,
            "take_profit": t.take_profit,
            "quantity": t.quantity,
            "exit_price": t.exit_price,
            "is_open": t.is_open,
            "notes": t.notes,
            "entry_time": t.entry_time.isoformat() if t.entry_time else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trades
    ]


@router.post("/trades/")
async def create_trade(trade: TradeCreate, db: Session = Depends(get_db)):
    # Use (or lazily create) the default paper account.
    from app.services.account_service import get_or_create_default_account
    account = get_or_create_default_account(db)

    try:
        new_trade = open_paper_position(
            db,
            account,
            symbol=trade.symbol,
            side=trade.trade_type,
            quantity=trade.quantity,
            price=trade.entry_price,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            notes=trade.notes,
        )
    except InsufficientBalance as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.commit()
    db.refresh(new_trade)

    return {
        "id": new_trade.id,
        "symbol": new_trade.symbol,
        "trade_type": new_trade.trade_type.value if hasattr(new_trade.trade_type, 'value') else new_trade.trade_type,
        "entry_price": new_trade.entry_price,
        "stop_loss": new_trade.stop_loss,
        "take_profit": new_trade.take_profit,
        "quantity": new_trade.quantity,
        "is_open": new_trade.is_open,
        "notes": new_trade.notes,
    }


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

    return {
        "id": trade.id,
        "symbol": trade.symbol,
        "trade_type": trade.trade_type.value if hasattr(trade.trade_type, 'value') else trade.trade_type,
        "entry_price": trade.entry_price,
        "stop_loss": trade.stop_loss,
        "take_profit": trade.take_profit,
        "quantity": trade.quantity,
        "is_open": trade.is_open,
        "notes": trade.notes,
    }


@router.delete("/trades/{trade_id}")
async def close_trade(trade_id: int, body: Optional[TradeClose] = None, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    trade.is_open = False
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
