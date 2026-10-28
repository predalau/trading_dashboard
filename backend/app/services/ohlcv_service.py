"""Historical OHLCV ingestion + retrieval for backtesting.

Fetches klines from Binance (public), paginating over a time range, and upserts
them into the ohlcv table. An httpx client is injectable for tests.
"""
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models import OHLCV

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000, "1w": 604_800_000,
}


async def fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int,
                       client: Optional[httpx.AsyncClient] = None) -> list[dict]:
    step = INTERVAL_MS.get(interval, 3_600_000)
    out: list[dict] = []

    async def _run(c: httpx.AsyncClient) -> None:
        cur = start_ms
        while cur < end_ms:
            params = {"symbol": symbol, "interval": interval,
                      "startTime": cur, "endTime": end_ms, "limit": 1000}
            resp = await c.get(BINANCE_KLINES, params=params)
            data = resp.json()
            if not data:
                break
            for k in data:
                out.append({
                    "ts": int(k[0]), "open": float(k[1]), "high": float(k[2]),
                    "low": float(k[3]), "close": float(k[4]), "volume": float(k[5]),
                })
            cur = int(data[-1][0]) + step
            if len(data) < 1000:
                break

    if client is not None:
        await _run(client)
    else:
        async with httpx.AsyncClient(timeout=20) as c:
            await _run(c)
    return out


def upsert_ohlcv(db: Session, symbol: str, timeframe: str, bars: list[dict]) -> int:
    if not bars:
        return 0
    tss = [b["ts"] for b in bars]
    existing = {
        row[0] for row in db.query(OHLCV.ts).filter(
            OHLCV.symbol == symbol, OHLCV.timeframe == timeframe, OHLCV.ts.in_(tss)
        )
    }
    added = 0
    for b in bars:
        if b["ts"] in existing:
            continue
        db.add(OHLCV(symbol=symbol, timeframe=timeframe, ts=b["ts"],
                     open=b["open"], high=b["high"], low=b["low"],
                     close=b["close"], volume=b["volume"]))
        added += 1
    db.commit()
    return added


async def backfill(db: Session, symbol: str, timeframe: str, start_ms: int, end_ms: int,
                   client: Optional[httpx.AsyncClient] = None) -> int:
    bars = await fetch_klines(symbol, timeframe, start_ms, end_ms, client=client)
    return upsert_ohlcv(db, symbol, timeframe, bars)


def get_ohlcv(db: Session, symbol: str, timeframe: str,
              start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> list[dict]:
    q = db.query(OHLCV).filter(OHLCV.symbol == symbol, OHLCV.timeframe == timeframe)
    if start_ms is not None:
        q = q.filter(OHLCV.ts >= start_ms)
    if end_ms is not None:
        q = q.filter(OHLCV.ts <= end_ms)
    rows = q.order_by(OHLCV.ts).all()
    return [{"ts": r.ts, "open": r.open, "high": r.high, "low": r.low,
             "close": r.close, "volume": r.volume} for r in rows]
