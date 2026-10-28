"""Watch-only wallet management (dashboard). Mounted at /api/v1."""
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Wallet

router = APIRouter()

_SOLANA_ADDR = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")


class WalletCreate(BaseModel):
    address: str
    chain: str = "solana"
    label: Optional[str] = None


class WalletResponse(BaseModel):
    id: int
    chain: str
    address: str
    label: Optional[str]
    is_watch_only: bool

    class Config:
        from_attributes = True


@router.post("/wallets", response_model=WalletResponse)
def add_wallet(w: WalletCreate, db: Session = Depends(get_db)):
    if w.chain == "solana" and not _SOLANA_ADDR.fullmatch(w.address):
        raise HTTPException(status_code=400, detail="Invalid Solana address")
    existing = (
        db.query(Wallet)
        .filter(Wallet.chain == w.chain, Wallet.address == w.address)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Wallet already tracked")
    row = Wallet(chain=w.chain, address=w.address, label=w.label, is_watch_only=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/wallets", response_model=List[WalletResponse])
def list_wallets(db: Session = Depends(get_db)):
    return db.query(Wallet).order_by(Wallet.id).all()


@router.delete("/wallets/{wallet_id}")
def delete_wallet(wallet_id: int, db: Session = Depends(get_db)):
    row = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Wallet not found")
    db.delete(row)
    db.commit()
    return {"message": "deleted", "id": wallet_id}
