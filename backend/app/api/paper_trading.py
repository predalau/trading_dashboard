from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Trade, Order, PaperTradingAccount, TradeType, OrderStatus
from app.services.trading_service import TradingService

router = APIRouter()


# Pydantic schemas
class TradeCreate(BaseModel):
    symbol: str
    exchange: str
    trade_type: TradeType
    entry_price: float
    quantity: float
    notes: Optional[str] = None


class TradeUpdate(BaseModel):
    exit_price: float
    notes: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    symbol: str
    exchange: str
    trade_type: TradeType
    entry_price: float
    quantity: float
    entry_time: datetime
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    profit_loss: Optional[float]
    profit_loss_percentage: Optional[float]
    is_open: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    account_name: str
    initial_balance: float


class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_name: str
    initial_balance: float
    current_balance: float
    available_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/accounts", response_model=AccountResponse)
async def create_account(
    account: AccountCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create a new paper trading account"""
    new_account = PaperTradingAccount(
        user_id=user_id,
        account_name=account.account_name,
        initial_balance=account.initial_balance,
        current_balance=account.initial_balance,
        available_balance=account.initial_balance
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account details"""
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == account_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/trades/{account_id}", response_model=TradeResponse)
async def create_trade(
    account_id: int,
    trade: TradeCreate,
    db: Session = Depends(get_db)
):
    """Create a new trade in paper trading account"""
    trading_service = TradingService(db)

    # Verify account exists
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == account_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Create trade
    new_trade = Trade(
        account_id=account_id,
        symbol=trade.symbol,
        exchange=trade.exchange,
        trade_type=trade.trade_type,
        entry_price=trade.entry_price,
        quantity=trade.quantity,
        notes=trade.notes
    )

    # Update account balance
    if trade.trade_type == TradeType.BUY:
        cost = trade.entry_price * trade.quantity
        if cost > account.available_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance for this trade"
            )
        account.available_balance -= cost

    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)
    return new_trade


@router.get("/trades/{account_id}", response_model=List[TradeResponse])
async def get_trades(
    account_id: int,
    is_open: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all trades for an account"""
    query = db.query(Trade).filter(Trade.account_id == account_id)

    if is_open is not None:
        query = query.filter(Trade.is_open == is_open)

    return query.all()


@router.put("/trades/{trade_id}", response_model=TradeResponse)
async def close_trade(
    trade_id: int,
    trade_update: TradeUpdate,
    db: Session = Depends(get_db)
):
    """Close a trade and calculate P&L"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if not trade.is_open:
        raise HTTPException(status_code=400, detail="Trade is already closed")

    # Calculate profit/loss
    profit_loss = (trade_update.exit_price - trade.entry_price) * trade.quantity
    profit_loss_percentage = ((trade_update.exit_price - trade.entry_price) / trade.entry_price) * 100

    # Update trade
    trade.exit_price = trade_update.exit_price
    trade.exit_time = datetime.utcnow()
    trade.profit_loss = profit_loss
    trade.profit_loss_percentage = profit_loss_percentage
    trade.is_open = False
    trade.notes = trade_update.notes or trade.notes

    # Update account balance
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == trade.account_id
    ).first()
    if account:
        proceeds = trade_update.exit_price * trade.quantity
        account.available_balance += proceeds
        account.current_balance = account.available_balance

    db.commit()
    db.refresh(trade)
    return trade


@router.get("/portfolio/{account_id}")
async def get_portfolio(account_id: int, db: Session = Depends(get_db)):
    """Get portfolio summary for account"""
    account = db.query(PaperTradingAccount).filter(
        PaperTradingAccount.id == account_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    open_trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.is_open == True
    ).all()

    closed_trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.is_open == False
    ).all()

    total_profit_loss = sum(t.profit_loss for t in closed_trades if t.profit_loss)

    return {
        "account": account,
        "open_trades_count": len(open_trades),
        "closed_trades_count": len(closed_trades),
        "total_realized_profit_loss": total_profit_loss,
        "cash_balance": account.available_balance
    }
