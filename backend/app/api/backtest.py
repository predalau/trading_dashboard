"""Backtest API: run strategies over cached OHLCV. Mounted at /api/v1/backtest.

v1 runs synchronously. If the requested OHLCV window isn't cached, it is
backfilled from Binance on demand.
"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.backtest.engine import run as run_engine
from app.backtest.registry import load_strategy
from app.backtest.param_spec import describe_params
from app.database import get_db
from app.deps.auth import get_api_key, require_scope
from app.models import ApiKey, Backtest, StrategyDef
from app.services.ohlcv_service import INTERVAL_MS, backfill, get_ohlcv
from app.services.strategy_authoring import StrategyValidationError, create_strategy

router = APIRouter()


class StrategyCreate(BaseModel):
    slug: str
    name: str
    source: str
    params: dict = {}
    description: Optional[str] = None


class RunRequest(BaseModel):
    module: Optional[str] = None           # e.g. strategies.sma_cross
    strategy_slug: Optional[str] = None    # or reference a registered strategy
    symbol: str
    timeframe: str = "1h"
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    lookback: int = 500                    # bars if start_ms not given
    params: dict = {}
    initial_cash: float = 10_000.0
    fee_bps: float = 10.0
    slippage_bps: float = 5.0


def _now_ms() -> int:
    return int(time.time() * 1000)


def _builtin_modules() -> list[str]:
    """Strategy modules shipped on disk (under the strategies package)."""
    import pkgutil
    import strategies
    return [f"strategies.{m.name}" for m in pkgutil.iter_modules(strategies.__path__)
            if m.name != "base"]


@router.get("/strategies")
def list_strategies(db: Session = Depends(get_db)):
    rows = db.query(StrategyDef).order_by(StrategyDef.id.desc()).all()

    entries = []
    by_module = {}
    for s in rows:
        e = {"id": s.id, "slug": s.slug, "name": s.name, "module": s.module,
             "params": s.params or {}, "description": s.description}
        entries.append(e)
        by_module[s.module] = e

    # Include built-in strategies that have no DB row (e.g. strategies.sma_cross)
    for module in _builtin_modules():
        if module in by_module:
            continue
        slug = module.split(".")[-1]
        entries.append({"id": None, "slug": slug, "name": slug, "module": module,
                        "params": {}, "description": "built-in strategy"})

    # Attach effective params + a param spec (declared or auto-derived) for the UI
    for e in entries:
        try:
            strat = load_strategy(e["module"], e["params"])
            e["params"] = strat.params
            e["param_spec"] = describe_params(strat)
        except Exception:
            e["param_spec"] = []
    return entries


@router.post("/strategies")
def author_strategy(body: StrategyCreate, key: ApiKey = Depends(get_api_key),
                    db: Session = Depends(get_db)):
    """Create/update a Python strategy (AST-validated). Requires 'strategy:write'."""
    require_scope(key, "strategy:write")
    try:
        row = create_strategy(db, slug=body.slug, name=body.name, source=body.source,
                              params=body.params, description=body.description)
    except StrategyValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"id": row.id, "slug": row.slug, "module": row.module, "name": row.name}


@router.post("/run")
async def run_backtest(body: RunRequest, db: Session = Depends(get_db)):
    # Resolve the strategy module + params (explicit module, or a registered slug).
    module = body.module
    params = dict(body.params or {})
    strategy_id = None
    if body.strategy_slug:
        sdef = db.query(StrategyDef).filter(StrategyDef.slug == body.strategy_slug).first()
        if not sdef:
            raise HTTPException(status_code=404, detail="strategy slug not found")
        module = sdef.module
        strategy_id = sdef.id
        params = {**(sdef.params or {}), **params}
    if not module:
        raise HTTPException(status_code=400, detail="module or strategy_slug required")

    interval_ms = INTERVAL_MS.get(body.timeframe)
    if not interval_ms:
        raise HTTPException(status_code=400, detail=f"unsupported timeframe: {body.timeframe}")

    end_ms = body.end_ms or _now_ms()
    start_ms = body.start_ms or (end_ms - body.lookback * interval_ms)

    bt = Backtest(strategy_id=strategy_id, symbol=body.symbol, timeframe=body.timeframe,
                  start_ts=start_ms, end_ts=end_ms, params=params, status="pending")
    db.add(bt)
    db.commit()
    db.refresh(bt)

    try:
        bars = get_ohlcv(db, body.symbol, body.timeframe, start_ms, end_ms)
        if len(bars) < 2:
            await backfill(db, body.symbol, body.timeframe, start_ms, end_ms)
            bars = get_ohlcv(db, body.symbol, body.timeframe, start_ms, end_ms)
        if len(bars) < 2:
            raise ValueError("no OHLCV data available for this symbol/timeframe/range")

        strategy = load_strategy(module, params)
        result = run_engine(bars, strategy, initial_cash=body.initial_cash,
                            fee_bps=body.fee_bps, slippage_bps=body.slippage_bps)
        bt.metrics = result["metrics"]
        bt.equity_curve = result["equity_curve"]
        bt.status = "done"
        db.commit()
        db.refresh(bt)
    except Exception as exc:
        bt.status = "error"
        bt.error = str(exc)[:1000]
        db.commit()
        raise HTTPException(status_code=400, detail=f"backtest failed: {exc}")

    return {"id": bt.id, "status": bt.status, "symbol": bt.symbol,
            "timeframe": bt.timeframe, "bars": len(bars), "metrics": bt.metrics}


@router.get("/{backtest_id}")
def get_backtest(backtest_id: int, db: Session = Depends(get_db)):
    bt = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not bt:
        raise HTTPException(status_code=404, detail="backtest not found")
    return {"id": bt.id, "strategy_id": bt.strategy_id, "symbol": bt.symbol,
            "timeframe": bt.timeframe, "start_ts": bt.start_ts, "end_ts": bt.end_ts,
            "params": bt.params, "status": bt.status, "metrics": bt.metrics,
            "equity_curve": bt.equity_curve, "error": bt.error}


@router.get("")
def list_backtests(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Backtest).order_by(Backtest.id.desc()).limit(min(limit, 200)).all()
    return [{"id": b.id, "symbol": b.symbol, "timeframe": b.timeframe,
             "status": b.status, "metrics": b.metrics, "created_at": b.created_at.isoformat() if b.created_at else None}
            for b in rows]
