from app.backtest.engine import run
from strategies.base import Strategy, Signal


class AlwaysLong(Strategy):
    def on_bar(self, i, bars):
        return Signal("BUY") if i == 0 else None


class BuyThenSell(Strategy):
    def on_bar(self, i, bars):
        if i == 0:
            return Signal("BUY")
        if i == len(bars) - 1:
            return Signal("SELL")
        return None


def _bars(closes):
    return [{"ts": i, "open": c, "high": c, "low": c, "close": c, "volume": 1.0}
            for i, c in enumerate(closes)]


def test_always_long_profits_on_rising_series():
    bars = _bars([100, 110, 120, 130, 140])
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0)
    # Bought at 100, held to 140 -> +40%
    assert res["metrics"]["total_return"] > 0.39
    assert res["metrics"]["total_return"] <= res["metrics"]["buy_hold_return"] + 1e-9
    assert len(res["equity_curve"]) == 5


def test_fees_reduce_return():
    bars = _bars([100, 100, 100, 100])
    res = run(bars, BuyThenSell(), initial_cash=10_000, fee_bps=10, slippage_bps=5)
    # Flat price but round-trip fees+slippage -> small loss, exactly one closed trade
    assert res["metrics"]["num_trades"] == 1
    assert res["metrics"]["total_return"] < 0


def test_metrics_shape_and_drawdown_sign():
    bars = _bars([100, 120, 90, 130])
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0)
    m = res["metrics"]
    for key in ("total_return", "buy_hold_return", "max_drawdown", "sharpe", "num_trades", "win_rate"):
        assert key in m
    assert m["max_drawdown"] <= 0.0


def test_trades_record_entry_and_exit_events():
    bars = _bars([100, 110, 120, 130])
    res = run(bars, BuyThenSell(), initial_cash=10_000, fee_bps=0, slippage_bps=0)
    assert len(res["trades"]) == 1
    t = res["trades"][0]
    assert t["entry_ts"] == 0 and t["entry_price"] == 100
    assert t["exit_ts"] == 3 and t["exit_price"] == 130
    assert t["pnl"] > 0


def test_open_position_at_end_has_entry_but_no_exit():
    bars = _bars([100, 110, 120])
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0)
    assert len(res["trades"]) == 1
    t = res["trades"][0]
    assert t["entry_ts"] == 0
    assert t["exit_ts"] is None and t["pnl"] is None   # still open -> not counted as closed
    assert res["metrics"]["num_trades"] == 0
