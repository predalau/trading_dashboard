"""Real Solana swaps via Jupiter — NON-CUSTODIAL.

Flow: /quote (read) -> /swap/prepare (unsigned tx for the user's wallet) ->
client signs in Phantom -> /swap/submit (we broadcast the signed tx and record
an order). The backend never holds a private key here. Mounted at /api/v1/solana
(behind the dashboard's basic-auth).
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, OrderStatus, TradeType
from app.services.account_service import get_or_create_default_account
from app.services.jupiter_service import JupiterError, JupiterService
from app.services.solana_service import SolanaService

router = APIRouter()


# Overridable in tests via app.dependency_overrides.
def get_jupiter() -> JupiterService:
    return JupiterService()


def get_solana() -> SolanaService:
    return SolanaService()


class QuoteRequest(BaseModel):
    input_mint: str
    output_mint: str
    amount: int            # base units of input mint
    slippage_bps: int = 50


class PrepareRequest(QuoteRequest):
    user_pubkey: str


class SubmitRequest(BaseModel):
    signed_transaction: str   # base64, signed by the user's wallet
    input_mint: str
    output_mint: str
    in_amount: float = 0.0    # UI amount, for the order record
    user_pubkey: Optional[str] = None


@router.post("/quote")
async def quote(body: QuoteRequest, jup: JupiterService = Depends(get_jupiter)):
    try:
        q = await jup.get_quote(body.input_mint, body.output_mint, body.amount, body.slippage_bps)
    except JupiterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"in_amount": q.get("inAmount"), "out_amount": q.get("outAmount"),
            "price_impact_pct": q.get("priceImpactPct"), "slippage_bps": q.get("slippageBps"),
            "quote": q}


@router.post("/swap/prepare")
async def prepare(body: PrepareRequest, jup: JupiterService = Depends(get_jupiter)):
    try:
        q = await jup.get_quote(body.input_mint, body.output_mint, body.amount, body.slippage_bps)
        tx = await jup.build_swap_tx(q, body.user_pubkey)
    except JupiterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"swap_transaction": tx["swap_transaction"],
            "last_valid_block_height": tx["last_valid_block_height"],
            "in_amount": q.get("inAmount"), "out_amount": q.get("outAmount")}


@router.post("/swap/submit")
async def submit(body: SubmitRequest, db: Session = Depends(get_db),
                 sol: SolanaService = Depends(get_solana)):
    try:
        signature = await sol.send_transaction(body.signed_transaction)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"broadcast failed: {exc}")

    # Best-effort confirmation poll (check-then-sleep so it's instant in tests).
    status = None
    for _ in range(8):
        try:
            status = await sol.get_signature_status(signature)
        except Exception:
            status = None
        if status in ("confirmed", "finalized", "failed"):
            break
        await asyncio.sleep(1.5)

    account = get_or_create_default_account(db)
    order_status = (OrderStatus.FILLED if status in ("confirmed", "finalized")
                    else OrderStatus.CANCELLED if status == "failed"
                    else OrderStatus.PENDING)
    order = Order(
        account_id=account.id,
        symbol=f"{body.input_mint[:6]}->{body.output_mint[:6]}",
        exchange="jupiter", order_type="SWAP", side=TradeType.SELL,
        quantity=body.in_amount or 0.0, status=order_status,
        mode="solana", tx_signature=signature,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"signature": signature, "status": status or "submitted",
            "order_id": order.id, "explorer": f"https://solscan.io/tx/{signature}"}
