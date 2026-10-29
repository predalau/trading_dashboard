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


def test_avg_trade_return_is_mean_per_trade_gain():
    # buy bar0 @100, sell last @120 -> one trade, +20%
    bars = _bars([100, 100, 110, 120])
    res = run(bars, BuyThenSell(), initial_cash=10_000, fee_bps=0, slippage_bps=0)
    m = res["metrics"]
    assert m["num_trades"] == 1
    assert abs(m["avg_trade_return"] - 0.20) < 1e-9
    assert m["avg_trade_pnl"] > 0


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


def test_bias_blocks_entry_below_threshold():
    bars = _bars([100, 110, 120, 130, 140])
    neg_bias = [-1.0] * len(bars)   # higher timeframes bearish everywhere
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0,
              bias=neg_bias, entry_threshold=0.0)
    assert res["metrics"]["num_trades"] == 0  # entry suppressed
    assert res["trades"] == []


def test_bias_allows_entry_when_aligned():
    bars = _bars([100, 110, 120, 130, 140])
    pos_bias = [1.0] * len(bars)
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0,
              bias=pos_bias, entry_threshold=0.0)
    assert res["metrics"]["total_return"] > 0  # allowed, rides the uptrend


def test_bias_force_exit_on_strong_flip():
    bars = _bars([100, 110, 120, 130, 140])
    # bullish early (enter), then strongly bearish at bar 2 -> force exit
    b = [1.0, 1.0, -1.0, -1.0, -1.0]
    res = run(bars, AlwaysLong(), initial_cash=10_000, fee_bps=0, slippage_bps=0,
              bias=b, entry_threshold=0.0, exit_threshold=-0.5)
    assert len(res["trades"]) == 1
    assert res["trades"][0]["exit_ts"] == 2   # forced out at the flip bar
