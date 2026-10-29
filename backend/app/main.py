from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from app.api import paper_trading, market_data, user, trades, bot, wallets, portfolio, backtest, solana_trade

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Dashboard API",
    description="API for paper trading and market data aggregation",
    version="0.1.0"
)

# CORS middleware
# Allow all origins in development, restrict in production
allow_origins = [
    "http://localhost:5173",      # Local Vite dev server
    "http://localhost:5174",      # Docker Vite dev server
    "http://localhost:3000",      # Alternative local port
    "http://localhost",           # Local machine
]

# In production, configure your domain
import os
if os.getenv("PRODUCTION_DOMAIN"):
    allow_origins.append(os.getenv("PRODUCTION_DOMAIN"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(paper_trading.router, prefix="/api/v1/paper-trading", tags=["Paper Trading"])
app.include_router(market_data.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(user.router, prefix="/api/v1/user", tags=["User"])
app.include_router(trades.router, prefix="/api/v1", tags=["Trades"])
app.include_router(bot.router, prefix="/api/v1/bot", tags=["Bot"])
app.include_router(wallets.router, prefix="/api/v1", tags=["Wallets"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["Backtest"])
app.include_router(solana_trade.router, prefix="/api/v1/solana", tags=["Solana"])


from app.database import SessionLocal
from app.services.account_service import get_or_create_default_account


@app.on_event("startup")
def _bootstrap_default_account():
    """Ensure the default operator user + paper account exist on boot."""
    db = SessionLocal()
    try:
        get_or_create_default_account(db)
    finally:
        db.close()


@app.on_event("startup")
async def _start_pending_order_poller():
    """Background watcher: fill pending (limit/stop) orders even with no browser open.

    Polls every PENDING_POLL_SEC seconds (0 disables). Does not fire during unit
    tests, which instantiate the app without the startup lifecycle.
    """
    import asyncio
    import os

    interval = int(os.getenv("PENDING_POLL_SEC", "15"))
    if interval <= 0:
        return

    async def _loop():
        from app.services.market_service import MarketService
        from app.services.pending_orders import process_pending_orders
        while True:
            await asyncio.sleep(interval)
            db = SessionLocal()
            try:
                result = await process_pending_orders(db, MarketService())
                if result.get("filled") or result.get("cancelled"):
                    logger.info(f"pending poller: {result}")
            except Exception as exc:
                logger.warning(f"pending poller error: {exc}")
            finally:
                db.close()

    asyncio.create_task(_loop())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Trading Dashboard API",
        "version": "0.1.0",
        "endpoints": {
            "paper_trading": "/api/v1/paper-trading",
            "market_data": "/api/v1/market",
            "user": "/api/v1/user"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
