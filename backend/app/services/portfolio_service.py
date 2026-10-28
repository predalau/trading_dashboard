"""Unified portfolio: paper equity (marked to market) + watch-only wallet values.

External services are injectable so the summary can be unit-tested without
network. All values are USD.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Trade, Wallet
from app.services.account_service import get_or_create_default_account
from app.services.market_service import MarketService
from app.services.paper_accounting import realized_pl
from app.services.pricing_service import PricingService
from app.services.solana_service import SOL_MINT, SolanaService


async def build_summary(
    db: Session,
    *,
    solana: Optional[SolanaService] = None,
    pricing: Optional[PricingService] = None,
    market: Optional[MarketService] = None,
) -> dict:
    solana = solana or SolanaService()
    pricing = pricing or PricingService()
    market = market or MarketService()

    account = get_or_create_default_account(db)

    # --- paper side: mark open positions to market ---
    open_trades = (
        db.query(Trade)
        .filter(Trade.account_id == account.id, Trade.is_open.is_(True))
        .all()
    )
    positions = []
    unrealized_total = 0.0
    for t in open_trades:
        mark = t.entry_price
        try:
            mark = (await market.get_price(t.symbol))["price"]
        except Exception:
            pass
        upl, _ = realized_pl(t.trade_type, t.entry_price, mark, t.quantity)
        unrealized_total += upl
        positions.append({
            "id": t.id,
            "symbol": t.symbol,
            "side": t.trade_type.value if hasattr(t.trade_type, "value") else t.trade_type,
            "quantity": t.quantity,
            "entry_price": t.entry_price,
            "mark_price": mark,
            "unrealized_pl": upl,
        })
    paper_equity = account.current_balance + unrealized_total

    # --- wallet side: Solana balances valued via Jupiter ---
    wallets_out = []
    wallets_total = 0.0
    for w in db.query(Wallet).order_by(Wallet.id).all():
        if w.chain != "solana":
            continue
        try:
            bal = await solana.get_wallet_balances(w.address)
            mints = [SOL_MINT] + [tk["mint"] for tk in bal["tokens"]]
            prices = await pricing.get_prices(mints)
            sol_price = prices.get(SOL_MINT, 0.0)
            wallet_value = bal["sol"] * sol_price
            tokens_out = []
            for tk in bal["tokens"]:
                price = prices.get(tk["mint"], 0.0)
                value = tk["amount"] * price
                wallet_value += value
                if value >= 0.01:  # hide dust / unpriced tokens from the UI
                    tokens_out.append({
                        "mint": tk["mint"], "amount": tk["amount"],
                        "price_usd": price, "value_usd": value,
                    })
            tokens_out.sort(key=lambda x: x["value_usd"], reverse=True)
            wallets_total += wallet_value
            wallets_out.append({
                "id": w.id, "address": w.address, "label": w.label,
                "sol": bal["sol"], "sol_price_usd": sol_price,
                "value_usd": wallet_value, "tokens": tokens_out,
            })
        except Exception:
            wallets_out.append({
                "id": w.id, "address": w.address, "label": w.label,
                "error": "fetch_failed", "value_usd": 0.0, "sol": 0.0, "tokens": [],
            })

    return {
        "paper": {
            "cash": account.available_balance,
            "equity": paper_equity,
            "unrealized_pl": unrealized_total,
            "open_positions": positions,
        },
        "wallets": wallets_out,
        "wallets_total_usd": wallets_total,
        "grand_total_usd": paper_equity + wallets_total,
    }
