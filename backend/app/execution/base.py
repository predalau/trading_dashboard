"""Execution venue abstraction shared by the UI, bots, and the MCP.

A venue takes a normalized OrderRequest and returns an OrderResult, persisting
an Order (audit/idempotency) and, for fills, a Trade (position). PaperVenue is
the only implementation today; SolanaVenue arrives in Phase 4.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderRequest:
    mode: str                       # paper | solana
    symbol: str
    side: str                       # BUY | SELL
    type: str = "MARKET"            # MARKET | LIMIT
    quantity: float = 0.0
    price: Optional[float] = None   # required for LIMIT; MARKET fills at last price
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    client_order_id: Optional[str] = None
    notes: Optional[str] = None
    api_key_id: Optional[int] = None


@dataclass
class OrderResult:
    order_id: int
    status: str
    mode: str
    symbol: str
    side: str
    quantity: float
    filled_price: Optional[float] = None
    trade_id: Optional[int] = None
    tx_signature: Optional[str] = None
    client_order_id: Optional[str] = None
    idempotent_replay: bool = False


class ExecutionVenue:
    async def place_order(self, db, req: OrderRequest, account) -> OrderResult:
        raise NotImplementedError
