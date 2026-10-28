from strategies.sma_cross import SmaCross


def _bars(closes):
    return [{"ts": i, "open": c, "high": c, "low": c, "close": c, "volume": 1.0}
            for i, c in enumerate(closes)]


def _signals(strategy, bars):
    out = []
    for i in range(len(bars)):
        s = strategy.on_bar(i, bars)
        if s:
            out.append((i, s.action))
    return out


def test_sma_cross_emits_buy_on_upcross():
    # Fall then rise -> fast SMA crosses above slow SMA at some point.
    closes = [10, 9, 8, 7, 6, 5, 6, 8, 10, 12, 14, 16]
    strat = SmaCross({"fast": 2, "slow": 3})
    actions = [a for _, a in _signals(strat, _bars(closes))]
    assert "BUY" in actions


def test_sma_cross_emits_sell_on_downcross():
    # Rise then fall -> fast SMA crosses below slow SMA.
    closes = [5, 6, 7, 8, 10, 12, 10, 8, 6, 4, 2, 1]
    strat = SmaCross({"fast": 2, "slow": 3})
    actions = [a for _, a in _signals(strat, _bars(closes))]
    assert "SELL" in actions


def test_params_default_and_override():
    assert SmaCross().params == {"fast": 10, "slow": 30}
    assert SmaCross({"fast": 5}).params == {"fast": 5, "slow": 30}
