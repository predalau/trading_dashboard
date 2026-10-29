"""Backtest API: run strategies over cached OHLCV. Mounted at /api/v1/backtest.

v1 runs synchronously. If the requested OHLCV window isn't cached, it is
backfilled from Binance on demand.
"""
import re
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


class ComboCreate(BaseModel):
    slug: str
    name: str
    threshold: float = 0.5
    components: list[dict] = []          # [{module, params, weight}]
    description: Optional[str] = None


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,48}$")


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

    # Attach params + param spec; drop built-in modules that aren't Strategy
    # subclasses (e.g. the indicators helper module).
    out = []
    for e in entries:
        try:
            strat = load_strategy(e["module"], e["params"])
        except Exception:
            if e["id"] is not None:   # keep (possibly broken) DB strategies; drop helpers
                e["param_spec"] = []
                out.append(e)
            continue
        e["params"] = strat.params
        e["param_spec"] = describe_params(strat)
        if e["id"] is None:   # enrich built-ins from the class metadata
            e["name"] = getattr(strat, "name", "") or e["name"]
            e["description"] = getattr(strat, "description", "") or e["description"]
        out.append(e)
    return out


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


@router.post("/combos")
def save_combo(body: ComboCreate, db: Session = Depends(get_db)):
    """Persist a weighted ensemble as a reusable strategy (StrategyDef).

    No API key required — this is the single-user dashboard's Save button.
    Re-saving the same slug updates it.
    """
    slug = body.slug.strip().lower()
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="invalid slug (use letters, digits, - or _)")
    if not body.components:
        raise HTTPException(status_code=400, detail="a combo needs at least one component")
    for c in body.components:
        module = c.get("module")
        if not module or not module.startswith("strategies."):
            raise HTTPException(status_code=400, detail=f"invalid component module: {module}")
        try:
            load_strategy(module, c.get("params") or {})
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"component {module} failed to load: {exc}")

    params = {"threshold": body.threshold, "components": body.components}
    row = db.query(StrategyDef).filter(StrategyDef.slug == slug).first()
    if row:
        row.name = body.name
        row.module = "strategies.ensemble"
        row.params = params
        row.description = body.description
    else:
        row = StrategyDef(slug=slug, name=body.name, module="strategies.ensemble",
                          params=params, description=body.description)
        db.add(row)
    db.commit()
    db.refresh(row)
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
        bt.trades = result["trades"]
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
            "equity_curve": bt.equity_curve, "trades": bt.trades, "error": bt.error}


@router.get("/{backtest_id}/ohlcv")
def get_backtest_ohlcv(backtest_id: int, db: Session = Depends(get_db)):
    """Price bars for a backtest's window (for the entry/exit chart)."""
    bt = db.query(Backtest).filter(Backtest.id == backtest_id).first()
    if not bt:
        raise HTTPException(status_code=404, detail="backtest not found")
    bars = get_ohlcv(db, bt.symbol, bt.timeframe, bt.start_ts, bt.end_ts)
    return {"symbol": bt.symbol, "timeframe": bt.timeframe,
            "bars": [{"ts": b["ts"], "open": b["open"], "high": b["high"],
                      "low": b["low"], "close": b["close"]} for b in bars]}


@router.get("")
def list_backtests(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Backtest).order_by(Backtest.id.desc()).limit(min(limit, 200)).all()
    return [{"id": b.id, "symbol": b.symbol, "timeframe": b.timeframe,
             "status": b.status, "metrics": b.metrics, "created_at": b.created_at.isoformat() if b.created_at else None}
            for b in rows]
