from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import MarketData
from app.services.market_service import MarketService

router = APIRouter()


class MarketDataResponse:
    def __init__(self, data):
        self.symbol = data.symbol
        self.exchange = data.exchange
        self.price = data.price
        self.volume_24h = data.volume_24h
        self.high_24h = data.high_24h
        self.low_24h = data.low_24h
        self.change_24h_percent = data.change_24h_percent
        self.timestamp = data.timestamp


@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    exchange: str = "BINANCE",
    db: Session = Depends(get_db)
):
    """Get latest price for a symbol"""
    market_service = MarketService()

    # Try to get from API
    try:
        price_data = await market_service.get_price(symbol, exchange)

        # Store in database
        market_data = MarketData(
            symbol=symbol,
            exchange=exchange,
            price=price_data.get("price"),
            volume_24h=price_data.get("volume_24h"),
            high_24h=price_data.get("high_24h"),
            low_24h=price_data.get("low_24h"),
            change_24h_percent=price_data.get("change_24h_percent")
        )
        db.add(market_data)
        db.commit()

        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
    exchange: str = "BINANCE"
):
    """Get candlestick data for a symbol"""
    market_service = MarketService()

    try:
        klines = await market_service.get_klines(symbol, interval, limit, exchange)
        return {
            "symbol": symbol,
            "interval": interval,
            "exchange": exchange,
            "klines": klines
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/24h/{symbol}")
async def get_24h_stats(
    symbol: str,
    exchange: str = "BINANCE"
):
    """Get 24h statistics for a symbol"""
    market_service = MarketService()

    try:
        stats = await market_service.get_24h_stats(symbol, exchange)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_supported_symbols(exchange: str = "BINANCE"):
    """Get list of supported symbols on an exchange"""
    market_service = MarketService()

    try:
        symbols = await market_service.get_symbols(exchange)
        return {
            "exchange": exchange,
            "symbols": symbols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
