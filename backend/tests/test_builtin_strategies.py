"""Smoke-test every built-in strategy: it loads and runs without crashing."""
import math

import pytest

from app.backtest.engine import run
from app.backtest.registry import load_strategy

BUILTINS = [
    "strategies.sma_cross", "strategies.ema_cross", "strategies.rsi",
    "strategies.macd", "strategies.bollinger", "strategies.donchian",
    "strategies.mean_reversion", "strategies.roc", "strategies.stochastic",
    "strategies.sma_trend",
]


def _bars(n=120):
    # a wavy series so oscillators/channels actually trigger
    out = []
    for i in range(n):
        c = 100 + 10 * math.sin(i / 5.0) + i * 0.1
        out.append({"ts": i * 3600_000, "open": c, "high": c + 1, "low": c - 1,
                    "close": c, "volume": 1.0})
    return out


@pytest.mark.parametrize("module", BUILTINS)
def test_builtin_strategy_runs(module):
    strat = load_strategy(module)
    res = run(_bars(), strat, initial_cash=10_000, fee_bps=10, slippage_bps=5)
    assert "metrics" in res and "trades" in res
    assert res["metrics"]["num_trades"] >= 0
    # every recorded trade has the event fields the chart needs
    for t in res["trades"]:
        assert "entry_ts" in t and "entry_price" in t
