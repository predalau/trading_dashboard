from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
from app.api import paper_trading, market_data, user

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
