from app.backtest.optimizer import (
    _param_values, _strategy_param_grid, enumerate_configs, config_hash,
)


def test_config_hash_is_stable_and_discriminating():
    a = {"module": "strategies.rsi", "params": {"period": 14, "oversold": 30},
         "symbol": "BTCUSDT", "timeframe": "1h", "lookback": 500, "bias": {"enabled": False}}
    # key order within params must not matter
    b = {"module": "strategies.rsi", "params": {"oversold": 30, "period": 14},
         "symbol": "BTCUSDT", "timeframe": "1h", "lookback": 500, "bias": {"enabled": False}}
    assert config_hash(a) == config_hash(b)
    c = dict(a, lookback=1000)
    assert config_hash(a) != config_hash(c)   # lookback changes the result -> different key


def test_param_values_samples_range_inclusive():
    p = {"type": "int", "min": 2, "max": 10, "default": 5}
    vals = _param_values(p, 3)
    assert vals[0] == 2 and vals[-1] == 10 and len(vals) == 3


def test_param_values_bool_and_choice():
    assert _param_values({"type": "bool"}, 7) == [False, True]
    assert _param_values({"type": "choice", "choices": ["a", "b"]}, 7) == ["a", "b"]


def test_strategy_param_grid_cartesian():
    spec = [
        {"name": "fast", "type": "int", "min": 2, "max": 4},
        {"name": "slow", "type": "int", "min": 10, "max": 20},
    ]
    grid = list(_strategy_param_grid(spec, 3))
    assert len(grid) == 9  # 3 x 3
    assert all("fast" in g and "slow" in g for g in grid)


def test_enumerate_configs_covers_axes():
    cfgs = enumerate_configs(None, ["BTCUSDT"], ["1h"], steps=2, lookback=300, bias_thresholds=[0.5])
    assert cfgs, "should produce configs"
    # every config is self-contained enough to re-run
    for c in cfgs[:20]:
        assert {"slug", "module", "params", "symbol", "timeframe", "lookback", "bias"} <= c.keys()
    # bias variants: off + on@0.5
    biases = {(c["bias"]["enabled"]) for c in cfgs}
    assert biases == {True, False}


def test_weight_vectors_deduped_by_ratio():
    from app.backtest.optimizer import _weight_vectors
    v = _weight_vectors(2, [1, 2, 3])
    assert [1, 1] in v
    assert [2, 2] not in v          # ratio-duplicate of (1,1)
    assert [1, 2] in v and [2, 1] in v


def test_combo_candidates_filters_min_trades_and_dedups_by_module(db_session):
    from app.backtest.optimizer import _combo_candidates
    from app.models import SweepResult
    rows = [
        ("a", "strategies.rsi", {"period": 7}, 10, 0.5),
        ("b", "strategies.rsi", {"period": 14}, 8, 0.4),   # same module, lower score
        ("c", "strategies.macd", {}, 2, 0.9),              # best score but too few trades
        ("d", "strategies.ema_cross", {"fast": 5}, 6, 0.3),
    ]
    for h, mod, params, nt, sc in rows:
        db_session.add(SweepResult(
            config_hash=h, module=mod, slug=mod.split(".")[-1], symbol="BTCUSDT",
            timeframe="1h", lookback=500, params=params, bias={"enabled": False},
            metrics={"num_trades": nt, "total_return": sc}, score=sc))
    db_session.commit()

    cands = _combo_candidates(db_session, "BTCUSDT", "1h", min_trades=3, top_n=8)
    mods = [c["module"] for c in cands]
    assert mods.count("strategies.rsi") == 1                 # deduped to best rsi
    assert cands[0]["params"] == {"period": 7}               # kept the higher-scoring one
    assert "strategies.macd" not in mods                     # filtered: 2 trades < 3
    assert "strategies.ema_cross" in mods
