"""Backtest API: run strategies over cached OHLCV. Mounted at /api/v1/backtest.

v1 runs synchronously. If the requested OHLCV window isn't cached, it is
backfilled from Binance on demand.
"""
import re
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Float, Integer, cast, func
from sqlalchemy.orm import Session

from app.backtest.engine import run as run_engine
from app.backtest.registry import load_strategy
from app.backtest.param_spec import describe_params
from app.backtest.trend_bias import build_bias_series, higher_timeframes
from app.database import get_db
from app.deps.auth import get_api_key, require_scope
from app.models import ApiKey, Backtest, SavedConfig, StrategyDef, Sweep, SweepResult
from app.services.ohlcv_service import INTERVAL_MS, backfill, ensure_ohlcv, get_ohlcv
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
    # Multi-timeframe trend bias (gates entries against higher-TF trend)
    bias_enabled: bool = False
    bias_sma_len: int = 50
    bias_entry_threshold: float = 0.0     # -1 = off .. +1 = require full HTF alignment
    bias_exit_enabled: bool = False
    bias_exit_threshold: float = -0.5     # force-close a long when HTF turns this bearish


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
        bars = await ensure_ohlcv(db, body.symbol, body.timeframe, start_ms, end_ms)
        if len(bars) < 2:
            raise ValueError("no OHLCV data available for this symbol/timeframe/range")

        strategy = load_strategy(module, params)

        # Optional multi-timeframe trend bias
        bias = None
        htfs = []
        if body.bias_enabled:
            bias, htfs = await build_bias_series(
                db, body.symbol, body.timeframe, bars, sma_len=body.bias_sma_len)
        result = run_engine(
            bars, strategy,
            initial_cash=body.initial_cash, fee_bps=body.fee_bps, slippage_bps=body.slippage_bps,
            bias=bias,
            entry_threshold=(body.bias_entry_threshold if body.bias_enabled else -1.0),
            exit_threshold=(body.bias_exit_threshold if (body.bias_enabled and body.bias_exit_enabled) else None),
        )
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
            "timeframe": bt.timeframe, "bars": len(bars), "metrics": bt.metrics,
            "trend_bias": {"enabled": body.bias_enabled, "higher_timeframes": htfs}}


class SweepRequest(BaseModel):
    lookback: int = 1000
    grid_steps: int = 7
    max_combos: int = 4000
    symbols: Optional[list[str]] = None
    timeframes: Optional[list[str]] = None
    bias_thresholds: list[float] = [0.0, 0.5]


@router.post("/sweep")
async def start_sweep(body: SweepRequest, db: Session = Depends(get_db)):
    """Launch a background parameter sweep; poll GET /sweep/{id} for progress."""
    import asyncio
    from app.backtest.optimizer import run_sweep, SYMBOLS, TIMEFRAMES

    sweep = Sweep(status="running", total=0, done=0, score_metric="total_return",
                  lookback=body.lookback)
    db.add(sweep)
    db.commit()
    db.refresh(sweep)

    asyncio.create_task(run_sweep(
        sweep.id,
        body.symbols or SYMBOLS,
        body.timeframes or TIMEFRAMES,
        body.grid_steps, body.lookback, body.max_combos, body.bias_thresholds,
    ))
    return {"id": sweep.id, "status": sweep.status}


class ComboSweepRequest(BaseModel):
    lookback: int = 1000
    max_combos: int = 8000
    min_trades: int = 3
    top_n: int = 8
    subset_min: int = 2
    subset_max: int = 5
    weights: list[int] = [1, 2, 3]
    thresholds: list[float] = [0.3, 0.5, 0.7]
    symbols: Optional[list[str]] = None
    timeframes: Optional[list[str]] = None


@router.post("/combo-sweep")
async def start_combo_sweep(body: ComboSweepRequest, db: Session = Depends(get_db)):
    """Discover ensembles from the best cached single-strategy configs."""
    import asyncio
    from app.backtest.optimizer import run_combo_sweep, SYMBOLS, TIMEFRAMES

    sweep = Sweep(status="running", total=0, done=0, score_metric="total_return",
                  lookback=body.lookback)
    db.add(sweep)
    db.commit()
    db.refresh(sweep)

    asyncio.create_task(run_combo_sweep(
        sweep.id,
        body.symbols or SYMBOLS,
        body.timeframes or TIMEFRAMES,
        body.lookback, body.max_combos, body.min_trades, body.top_n,
        body.subset_min, body.subset_max, body.weights, body.thresholds,
    ))
    return {"id": sweep.id, "status": sweep.status}


@router.get("/sweeps")
def list_sweeps(limit: int = 5, db: Session = Depends(get_db)):
    rows = db.query(Sweep).order_by(Sweep.id.desc()).limit(min(limit, 20)).all()
    return [{"id": s.id, "status": s.status, "total": s.total, "done": s.done,
             "created_at": s.created_at.isoformat() if s.created_at else None} for s in rows]


@router.get("/sweep/{sweep_id}")
def get_sweep(sweep_id: int, db: Session = Depends(get_db)):
    s = db.query(Sweep).filter(Sweep.id == sweep_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="sweep not found")
    return {"id": s.id, "status": s.status, "total": s.total, "done": s.done,
            "score_metric": s.score_metric, "lookback": s.lookback,
            "results": s.results or [], "error": s.error}


@router.post("/sweep/{sweep_id}/cancel")
def cancel_sweep(sweep_id: int, db: Session = Depends(get_db)):
    """Signal a running sweep to stop (it checks this flag every ~25 combos)."""
    s = db.query(Sweep).filter(Sweep.id == sweep_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="sweep not found")
    if s.status == "running":
        s.status = "cancelled"
        db.commit()
    return {"id": s.id, "status": s.status}


@router.get("/results")
def query_results(symbol: Optional[str] = None, timeframe: Optional[str] = None,
                  slug: Optional[str] = None, bias: Optional[str] = None,
                  min_trades: int = 3, min_avg_pct: float = 0.0,
                  limit: int = 100, db: Session = Depends(get_db)):
    """Filterable top results over the whole sweep cache (ranked by score).

    Low-sample strategies (< min_trades, default 3) are excluded, and
    min_avg_pct screens out tiny-edge configs whose average %/trade would be
    eaten by fees/taxes.
    """
    q = db.query(SweepResult)
    if symbol:
        q = q.filter(SweepResult.symbol == symbol)
    if timeframe:
        q = q.filter(SweepResult.timeframe == timeframe)
    if slug:
        q = q.filter(SweepResult.slug == slug)
    if bias == "on":
        q = q.filter(func.jsonb_extract_path_text(SweepResult.bias, "enabled") == "true")
    elif bias == "off":
        q = q.filter(func.jsonb_extract_path_text(SweepResult.bias, "enabled") == "false")
    if min_trades > 0:
        q = q.filter(
            cast(func.jsonb_extract_path_text(SweepResult.metrics, "num_trades"), Integer) >= min_trades)
    if min_avg_pct and min_avg_pct > 0:
        q = q.filter(
            cast(func.jsonb_extract_path_text(SweepResult.metrics, "avg_trade_return"), Float)
            >= (min_avg_pct / 100.0))
    rows = q.order_by(SweepResult.score.desc().nullslast()).limit(min(limit, 500)).all()
    return [{
        "config": {"slug": r.slug, "module": r.module, "params": r.params,
                   "symbol": r.symbol, "timeframe": r.timeframe,
                   "lookback": r.lookback, "bias": r.bias or {"enabled": False}},
        "metrics": r.metrics, "score": r.score,
    } for r in rows]


def _ser_saved(sc: SavedConfig) -> dict:
    return {"id": sc.id, "name": sc.name, "module": sc.module, "slug": sc.slug,
            "params": sc.params or {}, "symbol": sc.symbol, "timeframe": sc.timeframe,
            "lookback": sc.lookback, "bias": sc.bias or {"enabled": False},
            "created_at": sc.created_at.isoformat() if sc.created_at else None}


class SavedConfigCreate(BaseModel):
    name: str
    module: str
    slug: Optional[str] = None
    params: dict = {}
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    lookback: int = 500
    bias: dict = {"enabled": False}


@router.post("/saved-configs")
def save_config(body: SavedConfigCreate, db: Session = Depends(get_db)):
    """Create or overwrite (by name) a reusable backtest configuration."""
    name = (body.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    try:
        load_strategy(body.module, body.params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid config: {exc}")
    sc = db.query(SavedConfig).filter(SavedConfig.name == name).first()
    if sc is None:
        sc = SavedConfig(name=name)
        db.add(sc)
    sc.module = body.module
    sc.slug = body.slug or body.module.split(".")[-1]
    sc.params = body.params
    sc.symbol = body.symbol
    sc.timeframe = body.timeframe
    sc.lookback = body.lookback
    sc.bias = body.bias
    db.commit()
    db.refresh(sc)
    return _ser_saved(sc)


@router.get("/saved-configs")
def list_saved_configs(db: Session = Depends(get_db)):
    rows = db.query(SavedConfig).order_by(SavedConfig.id.desc()).all()
    return [_ser_saved(s) for s in rows]


@router.delete("/saved-configs/{config_id}")
def delete_saved_config(config_id: int, db: Session = Depends(get_db)):
    sc = db.query(SavedConfig).filter(SavedConfig.id == config_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="config not found")
    db.delete(sc)
    db.commit()
    return {"ok": True}


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
