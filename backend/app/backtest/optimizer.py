"""Parameter sweep (grid search) over backtest settings.

Enumerates built-in strategies × their param grids × symbols × timeframes ×
trend-bias variants, runs each through the engine (no DB rows created), and
keeps the top-N by a score metric. Runs as a background task; progress and
results are written to the Sweep row.
"""
import itertools
import random
import time

from app.backtest.engine import run as run_engine
from app.backtest.param_spec import describe_params
from app.backtest.registry import load_strategy
from app.backtest.trend_bias import build_bias_series
from app.models import Sweep
from app.services.ohlcv_service import INTERVAL_MS, backfill, get_ohlcv

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
TIMEFRAMES = ["15m", "1h", "4h", "1d"]


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

        for idx, cfg in enumerate(configs):
            sym, tf = cfg["symbol"], cfg["timeframe"]
            try:
                bars = bars_cache.get((sym, tf))
                if bars is None:
                    interval = INTERVAL_MS[tf]
                    start = now - lookback * interval
                    bars = get_ohlcv(db, sym, tf, start, now)
                    if len(bars) < min(lookback, 100):
                        await backfill(db, sym, tf, start, now)
                        bars = get_ohlcv(db, sym, tf, start, now)
                    bars_cache[(sym, tf)] = bars
                if len(bars) < 2:
                    continue

                bias_arr, entry_thr = None, -1.0
                if cfg["bias"]["enabled"]:
                    sma_len = cfg["bias"].get("sma_len", 50)
                    ckey = (sym, tf, sma_len)
                    if ckey not in bias_cache:
                        bias_cache[ckey], _ = await build_bias_series(db, sym, tf, bars, sma_len=sma_len)
                    bias_arr = bias_cache[ckey]
                    entry_thr = cfg["bias"].get("entry_threshold", 0.0)

                strat = load_strategy(cfg["module"], cfg["params"])
                res = run_engine(bars, strat, bias=bias_arr, entry_threshold=entry_thr)
                score = res["metrics"].get(score_metric)
                results.append({"config": cfg, "metrics": res["metrics"],
                                "score": score if score is not None else 0.0})
            except Exception:
                pass

            if idx % 25 == 0:
                sweep.done = idx
                db.commit()

        results.sort(key=lambda r: r["score"], reverse=True)
        sweep.results = results[:100]
        sweep.done = sweep.total
        sweep.status = "done"
        db.commit()
    except Exception as exc:
        sweep.status = "error"
        sweep.error = str(exc)[:1000]
        db.commit()
    finally:
        db.close()
