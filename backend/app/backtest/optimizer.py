"""Parameter sweep (grid search) over backtest settings.

Enumerates built-in strategies × their param grids × symbols × timeframes ×
trend-bias variants, runs each through the engine (no DB rows created), and
keeps the top-N by a score metric. Runs as a background task; progress and
results are written to the Sweep row.
"""
import asyncio
import hashlib
import itertools
import json
import random
import time
from functools import reduce
from math import gcd

from app.backtest.engine import run as run_engine
from app.backtest.param_spec import describe_params
from app.backtest.registry import load_strategy
from app.backtest.trend_bias import build_bias_series
from app.models import StrategyDef, Sweep, SweepResult
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


def _threshold_grid(steps: int) -> list[float]:
    n = max(2, steps)
    out, seen = [], set()
    for k in range(n):
        v = round(0.1 + (1.0 - 0.1) * k / (n - 1), 2)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def enumerate_configs(db, symbols, timeframes, steps, lookback, bias_thresholds) -> list[dict]:
    bias_variants: list[dict] = [{"enabled": False}]
    for t in bias_thresholds:
        bias_variants.append({"enabled": True, "sma_len": 50, "entry_threshold": t})

    # (slug, module, [param-dicts]) for every strategy to sweep
    strategy_grids: list[tuple[str, str, list[dict]]] = []

    # built-in single strategies -> full param grid
    for module in _builtin_strategy_modules():
        try:
            strat = load_strategy(module)
        except Exception:
            continue
        spec = describe_params(strat)
        grids = list(_strategy_param_grid(spec, steps)) or [{}]
        strategy_grids.append((module.split(".")[-1], module, grids))

    # saved combos -> sweep the ensemble threshold, components fixed as saved
    if db is not None:
        combos = db.query(StrategyDef).filter(StrategyDef.module == "strategies.ensemble").all()
        for c in combos:
            base = c.params or {}
            components = base.get("components") or []
            if not components:
                continue
            grids = [{"threshold": t, "components": components} for t in _threshold_grid(steps)]
            strategy_grids.append((c.slug, "strategies.ensemble", grids))

    configs = []
    for slug, module, grids in strategy_grids:
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


async def _execute_loop(db, sweep, configs, lookback, score_metric="total_return"):
    """Run each config (cache-aware), writing progress/results to the sweep row."""
    sweep.total = len(configs)
    db.commit()

    now = _now_ms()
    bars_cache: dict = {}
    bias_cache: dict = {}
    results = []
    cancelled = False

    for idx, cfg in enumerate(configs):
        sym, tf = cfg["symbol"], cfg["timeframe"]
        h = config_hash(cfg)

        cached = db.query(SweepResult).filter(SweepResult.config_hash == h).first()
        if cached:
            results.append({"config": cfg, "metrics": cached.metrics,
                            "score": cached.score if cached.score is not None else 0.0})
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
            except Exception:
                pass

        if idx % 25 == 0:
            sweep.done = idx
            try:
                db.commit()
            except Exception:
                db.rollback()
            db.refresh(sweep)
            if sweep.status == "cancelled":
                cancelled = True
                break
        await asyncio.sleep(0)

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


async def run_sweep(sweep_id: int, symbols, timeframes, steps, lookback,
                    max_combos, bias_thresholds, score_metric="total_return"):
    from app.database import SessionLocal
    db = SessionLocal()
    sweep = db.query(Sweep).filter(Sweep.id == sweep_id).first()
    if not sweep:
        db.close()
        return
    try:
        configs = enumerate_configs(db, symbols, timeframes, steps, lookback, bias_thresholds)
        random.Random(42).shuffle(configs)
        if len(configs) > max_combos:
            configs = configs[:max_combos]
        await _execute_loop(db, sweep, configs, lookback, score_metric)
    except Exception as exc:
        sweep.status = "error"
        sweep.error = str(exc)[:1000]
        db.commit()
    finally:
        db.close()


# ---- Combo discovery: build ensembles from the best single strategies ----

def _weight_vectors(size: int, weights: list[int]) -> list[list[int]]:
    """All weight vectors over `weights`, deduped by ratio (gcd-normalized)."""
    seen, out = set(), []
    for combo in itertools.product(weights, repeat=size):
        g = reduce(gcd, combo)
        norm = tuple(w // g for w in combo)
        if norm not in seen:
            seen.add(norm)
            out.append(list(norm))
    return out


def _combo_candidates(db, symbol, timeframe, min_trades, top_n) -> list[dict]:
    """Best single-strategy configs (one per strategy type) from the cache."""
    rows = (db.query(SweepResult)
            .filter(SweepResult.symbol == symbol, SweepResult.timeframe == timeframe,
                    SweepResult.module != "strategies.ensemble")
            .order_by(SweepResult.score.desc().nullslast()).limit(1000).all())
    seen, out = set(), []
    for r in rows:
        if r.module in seen:
            continue
        nt = (r.metrics or {}).get("num_trades") or 0
        if nt < min_trades:
            continue
        seen.add(r.module)
        out.append({"module": r.module, "params": r.params or {}})
        if len(out) >= top_n:
            break
    return out


def _iter_combo_configs(db, symbols, timeframes, lookback, min_trades, top_n,
                        subset_min, subset_max, weights, thresholds):
    for sym in symbols:
        for tf in timeframes:
            cands = _combo_candidates(db, sym, tf, min_trades, top_n)
            if len(cands) < subset_min:
                continue
            hi = min(subset_max, len(cands))
            for size in range(subset_min, hi + 1):
                wvs = _weight_vectors(size, weights)
                for subset in itertools.combinations(cands, size):
                    for wv in wvs:
                        for t in thresholds:
                            components = [{"module": c["module"], "params": c["params"], "weight": w}
                                          for c, w in zip(subset, wv)]
                            yield {
                                "slug": "auto-combo",
                                "module": "strategies.ensemble",
                                "params": {"threshold": t, "components": components},
                                "symbol": sym, "timeframe": tf, "lookback": lookback,
                                "bias": {"enabled": False},
                            }


def _reservoir_sample(iterable, k, seed=42):
    """Uniform sample of up to k items from a (possibly huge) iterator; O(k) memory."""
    rnd = random.Random(seed)
    res = []
    for i, item in enumerate(iterable):
        if i < k:
            res.append(item)
        else:
            j = rnd.randint(0, i)
            if j < k:
                res[j] = item
    return res


async def run_combo_sweep(sweep_id: int, symbols, timeframes, lookback, max_combos,
                          min_trades, top_n, subset_min, subset_max, weights, thresholds,
                          score_metric="total_return"):
    from app.database import SessionLocal
    db = SessionLocal()
    sweep = db.query(Sweep).filter(Sweep.id == sweep_id).first()
    if not sweep:
        db.close()
        return
    try:
        gen = _iter_combo_configs(db, symbols, timeframes, lookback, min_trades, top_n,
                                  subset_min, subset_max, weights, thresholds)
        configs = _reservoir_sample(gen, max_combos)
        await _execute_loop(db, sweep, configs, lookback, score_metric)
    except Exception as exc:
        sweep.status = "error"
        sweep.error = str(exc)[:1000]
        db.commit()
    finally:
        db.close()
