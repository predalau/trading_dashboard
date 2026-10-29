"""Multi-timeframe trend bias for the backtester.

For a base-timeframe run, derive a trend score from the higher timeframes above
it (price vs SMA on each) and aggregate into one score per base bar, in -1..+1
(+1 = all higher timeframes bullish, -1 = all bearish). The engine uses this to
gate entries (and optionally force exits). No lookahead: at each base bar we only
use higher-timeframe bars that have fully closed by that bar's close time.
"""
from app.services.ohlcv_service import INTERVAL_MS, backfill, get_ohlcv

LADDER = ["15m", "1h", "4h", "1d", "1w"]


def higher_timeframes(base: str, n: int = 2) -> list[str]:
    """The next `n` tradable timeframes above `base` on the ladder."""
    if base not in LADDER:
        return []
    i = LADDER.index(base)
    return [tf for tf in LADDER[i + 1:] if tf in INTERVAL_MS][:n]


def _trend_array(bars: list[dict], sma_len: int) -> list[int]:
    """+1 if close is above its SMA, -1 if below, 0 while warming up."""
    out = []
    closes = [b["close"] for b in bars]
    for j in range(len(bars)):
        if j + 1 < sma_len:
            out.append(0)
            continue
        sma = sum(closes[j + 1 - sma_len: j + 1]) / sma_len
        out.append(1 if closes[j] > sma else -1)
    return out


async def _ensure_ohlcv(db, symbol, tf, start, end, need):
    bars = get_ohlcv(db, symbol, tf, start, end)
    if len(bars) < need:
        await backfill(db, symbol, tf, start, end)
        bars = get_ohlcv(db, symbol, tf, start, end)
    return bars


async def build_bias_series(db, symbol: str, base_tf: str, base_bars: list[dict],
                            sma_len: int = 50, max_htfs: int = 2):
    """Return (bias_per_base_bar in -1..1, higher_timeframes_used)."""
    htfs = higher_timeframes(base_tf, max_htfs)
    if not htfs or not base_bars:
        return [0.0] * len(base_bars), []

    base_ms = INTERVAL_MS[base_tf]
    start = base_bars[0]["ts"]
    end = base_bars[-1]["ts"] + base_ms

    htf_data = []  # (interval_ms, bars, trend_array)
    for tf in htfs:
        ms = INTERVAL_MS[tf]
        warm_start = start - (sma_len + 2) * ms
        bars = await _ensure_ohlcv(db, symbol, tf, warm_start, end, sma_len + 2)
        htf_data.append((ms, bars, _trend_array(bars, sma_len)))

    # higher timeframes carry more weight (ladder order is ascending)
    weights = list(range(1, len(htfs) + 1))
    total_w = sum(weights)

    ptrs = [0] * len(htfs)
    out = []
    for b in base_bars:
        decision_t = b["ts"] + base_ms  # the base bar's close time
        score = 0.0
        for k, (ms, bars, trends) in enumerate(htf_data):
            if not bars:
                continue
            j = ptrs[k]
            # advance to the latest HTF bar fully closed by decision_t
            while j + 1 < len(bars) and bars[j + 1]["ts"] + ms <= decision_t:
                j += 1
            ptrs[k] = j
            closed = bars[j]["ts"] + ms <= decision_t
            score += weights[k] * (trends[j] if closed else 0)
        out.append(score / total_w if total_w else 0.0)
    return out, htfs
