"""Bot/MCP order API (API-key authenticated). Mounted at /api/v1/bot."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps.auth import get_api_key, get_rate_limited_api_key, require_scope
from app.execution import OrderRequest, SUPPORTED_MODES, get_venue
from app.models import ApiKey, Order
from app.services.account_service import get_or_create_default_account
from app.services.paper_accounting import InsufficientBalance

router = APIRouter()


class BotOrder(BaseModel):
    mode: str = "paper"          # paper | solana (solana = Phase 4)
    symbol: str
    side: str                    # BUY | SELL
    type: str = "MARKET"
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    client_order_id: Optional[str] = None
    notes: Optional[str] = None


def _scope_for_mode(mode: str) -> str:
    return "paper:write" if mode == "paper" else "real:write"


@router.post("/orders")
async def place_order(
    order: BotOrder,
    key: ApiKey = Depends(get_rate_limited_api_key),
    db: Session = Depends(get_db),
):
    # Scope first, so a paper-only key hitting a real venue gets 403 (not 400).
    require_scope(key, _scope_for_mode(order.mode))

    if order.mode not in SUPPORTED_MODES:
        raise HTTPException(status_code=400, detail=f"Mode not yet supported: {order.mode}")
    if order.side.upper() not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="side must be BUY or SELL")
    if order.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be > 0")

    account = get_or_create_default_account(db)
    req = OrderRequest(
        mode=order.mode,
        symbol=order.symbol,
        side=order.side.upper(),
        type=order.type,
        quantity=order.quantity,
        price=order.price,
        stop_loss=order.stop_loss,
        take_profit=order.take_profit,
        client_order_id=order.client_order_id,
        notes=order.notes,
        api_key_id=key.id,
    )
    try:
        result = await get_venue(order.mode).place_order(db, req, account)
    except InsufficientBalance as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result.__dict__


@router.get("/orders")
async def list_orders(
    limit: int = 50,
    key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
):
    """List orders placed by this API key (for bot reconciliation)."""
    rows = (
        db.query(Order)
        .filter(Order.api_key_id == key.id)
        .order_by(Order.id.desc())
        .limit(min(limit, 500))
        .all()
    )
    return [
        {
            "id": o.id,
            "mode": o.mode,
            "symbol": o.symbol,
            "side": o.side.value if hasattr(o.side, "value") else o.side,
            "quantity": o.quantity,
            "filled_price": o.filled_price,
            "status": o.status.value if hasattr(o.status, "value") else o.status,
            "client_order_id": o.client_order_id,
            "tx_signature": o.tx_signature,
        }
        for o in rows
    ]
