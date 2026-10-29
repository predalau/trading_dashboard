"""Parameter sweep (grid search) over backtest settings.

Enumerates built-in strategies × their param grids × symbols × timeframes ×
trend-bias variants, runs each through the engine (no DB rows created), and
keeps the top-N by a score metric. Runs as a background task; progress and
results are written to the Sweep row.
"""
import hashlib
import itertools
import json
import random
import time

from app.backtest.engine import run as run_engine
from app.backtest.param_spec import describe_params
from app.backtest.registry import load_strategy
from app.backtest.trend_bias import build_bias_series
from app.models import Sweep, SweepResult
from app.services.ohlcv_service import INTERVAL_MS, ensure_ohlcv

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
TIMEFRAMES = ["15m", "1h", "4h", "1d"]


def config_hash(cfg: dict) -> str:
    """Stable hash of everything that affects a backtest's result."""
    canon = {
        "module": cfg["module"],
        "params": cfg.get("params") or {},
        "symbol": cfg["symbol"],
        "timeframe": cfg["timeframe"],
        "lookback": cfg["lookback"],
        "bias": cfg.get("bias") or {"enabled": False},
    }
    s = json.dumps(canon, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode()).hexdigest()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _param_values(p: dict, steps: int) -> list:
    t = p.get("type")
    if t == "bool":
        return [False, True]
    if t == "choice":
        return list(p.get("choices") or [])
    lo, hi = p.get("min"), p.get("max")
    if lo is None or hi is None:
        d = p.get("default")
        return [d] if d is not None else []
    if steps <= 1 or lo == hi:
        return [p.get("default", lo)]
    out, seen = [], set()
    for k in range(steps):
        v = lo + (hi - lo) * k / (steps - 1)
        v = int(round(v)) if t == "int" else round(v, 4)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _strategy_param_grid(spec: list, steps: int):
    names = [p["name"] for p in spec]
    value_lists = [(_param_values(p, steps) or [None]) for p in spec]
    for combo in itertools.product(*value_lists):
        yield {n: v for n, v in zip(names, combo) if v is not None}


def _builtin_strategy_modules() -> list[str]:
    from app.api.backtest import _builtin_modules
    return [m for m in _builtin_modules() if m != "strategies.ensemble"]


def enumerate_configs(symbols, timeframes, steps, lookback, bias_thresholds) -> list[dict]:
    bias_variants: list[dict] = [{"enabled": False}]
    for t in bias_thresholds:
        bias_variants.append({"enabled": True, "sma_len": 50, "entry_threshold": t})

    configs = []
    for module in _builtin_strategy_modules():
        try:
            strat = load_strategy(module)
        except Exception:
            continue
        spec = describe_params(strat)
        slug = module.split(".")[-1]
        grids = list(_strategy_param_grid(spec, steps)) or [{}]
        for sym in symbols:
            for tf in timeframes:
                for params in grids:
                    for bias in bias_variants:
                        configs.append({
                            "slug": slug, "module": module, "params": params,
                            "symbol": sym, "timeframe": tf, "lookback": lookback,
                            "bias": bias,
                        })
    return configs


async def run_sweep(sweep_id: int, symbols, timeframes, steps, lookback,
                    max_combos, bias_thresholds, score_metric="total_return"):
    import asyncio
    from app.database import SessionLocal
    db = SessionLocal()
    sweep = db.query(Sweep).filter(Sweep.id == sweep_id).first()
    if not sweep:
        db.close()
        return
    try:
        configs = enumerate_configs(symbols, timeframes, steps, lookback, bias_thresholds)
        random.Random(42).shuffle(configs)
        if len(configs) > max_combos:
            configs = configs[:max_combos]
        sweep.total = len(configs)
        db.commit()

        now = _now_ms()
        bars_cache: dict = {}
        bias_cache: dict = {}
        results = []
        cancelled = False
        computed = 0
        reused = 0

        for idx, cfg in enumerate(configs):
            sym, tf = cfg["symbol"], cfg["timeframe"]
            h = config_hash(cfg)

            # Cache hit -> reuse, skip the backtest entirely
            cached = db.query(SweepResult).filter(SweepResult.config_hash == h).first()
            if cached:
                results.append({"config": cfg, "metrics": cached.metrics,
                                "score": cached.score if cached.score is not None else 0.0})
                reused += 1
            else:
                try:
                    bars = bars_cache.get((sym, tf))
                    if bars is None:
                        interval = INTERVAL_MS[tf]
                        start = now - lookback * interval
                        bars = await ensure_ohlcv(db, sym, tf, start, now)
                        bars_cache[(sym, tf)] = bars
                    if len(bars) >= 2:
                        bias_arr, entry_thr = None, -1.0
                        if cfg["bias"]["enabled"]:
                            sma_len = cfg["bias"].get("sma_len", 50)
                            ckey = (sym, tf, sma_len)
                            if ckey not in bias_cache:
                                bias_cache[ckey], _ = await build_bias_series(db, sym, tf, bars, sma_len=sma_len)
                            bias_arr = bias_cache[ckey]
                            entry_thr = cfg["bias"].get("entry_threshold", 0.0)

                        strat = load_strategy(cfg["module"], cfg["params"])
                        # run the CPU-bound backtest off the event loop so the API
                        # (cancel, dashboard, pending poller) stays responsive
                        res = await asyncio.to_thread(
                            run_engine, bars, strat, bias=bias_arr, entry_threshold=entry_thr)
                        metrics = res["metrics"]
                        score = metrics.get(score_metric)
                        score = score if score is not None else 0.0
                        db.add(SweepResult(
                            config_hash=h, module=cfg["module"], slug=cfg["slug"],
                            symbol=sym, timeframe=tf, lookback=lookback,
                            params=cfg["params"], bias=cfg["bias"],
                            metrics=metrics, score=score))
                        results.append({"config": cfg, "metrics": metrics, "score": score})
                        computed += 1
                except Exception:
                    pass

            if idx % 25 == 0:
                sweep.done = idx
                try:
                    db.commit()           # persist progress + any cached rows
                except Exception:
                    db.rollback()
                db.refresh(sweep)         # pick up an external cancel
                if sweep.status == "cancelled":
                    cancelled = True
                    break
            await asyncio.sleep(0)        # yield so the API stays responsive

        results.sort(key=lambda r: r["score"], reverse=True)
        sweep.results = results[:100]
        if cancelled:
            sweep.status = "cancelled"
        else:
            sweep.status = "done"
            sweep.done = sweep.total
        try:
            db.commit()
        except Exception:
            db.rollback()
            sweep.results = results[:100]
            sweep.status = "cancelled" if cancelled else "done"
            db.commit()
    except Exception as exc:
        sweep.status = "error"
        sweep.error = str(exc)[:1000]
        db.commit()
    finally:
        db.close()
