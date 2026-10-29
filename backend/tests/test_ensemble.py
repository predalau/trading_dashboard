from app.backtest.engine import run
from app.backtest.registry import load_strategy


def _bars(closes):
    return [{"ts": i * 3600_000, "open": c, "high": c, "low": c, "close": c, "volume": 1.0}
            for i, c in enumerate(closes)]


def test_ensemble_single_component_follows_its_stance():
    rising = list(range(100, 160))  # strict uptrend
    params = {"threshold": 0.5, "components": [
        {"module": "strategies.sma_trend", "params": {"period": 5}, "weight": 1}]}
    strat = load_strategy("strategies.ensemble", params)
    res = run(_bars(rising), strat, fee_bps=0, slippage_bps=0)
    assert res["metrics"]["total_return"] > 0  # stays long through the uptrend


def test_ensemble_impossible_threshold_never_trades():
    rising = list(range(100, 160))
    params = {"threshold": 1.5, "components": [
        {"module": "strategies.sma_trend", "params": {"period": 5}, "weight": 1}]}
    strat = load_strategy("strategies.ensemble", params)
    res = run(_bars(rising), strat, fee_bps=0, slippage_bps=0)
    assert res["metrics"]["num_trades"] == 0


def test_ensemble_weighted_threshold_needs_majority():
    # one always-long (sma_trend on uptrend) weight 1, threshold 0.6 -> 1/1 = 1.0 >= 0.6 long
    rising = list(range(100, 160))
    params = {"threshold": 0.6, "components": [
        {"module": "strategies.sma_trend", "params": {"period": 5}, "weight": 1}]}
    res = run(_bars(rising), load_strategy("strategies.ensemble", params), fee_bps=0, slippage_bps=0)
    assert res["metrics"]["total_return"] > 0


def test_save_combo_creates_reusable_strategy(client):
    r = client.post("/api/v1/backtest/combos", json={
        "slug": "my-combo", "name": "My Combo", "threshold": 0.5,
        "components": [{"module": "strategies.sma_cross", "params": {}, "weight": 1}]})
    assert r.status_code == 200, r.text
    assert r.json()["module"] == "strategies.ensemble"
    listed = client.get("/api/v1/backtest/strategies").json()
    assert any(s["slug"] == "my-combo" for s in listed)


def test_save_combo_rejects_empty_and_bad_slug(client):
    assert client.post("/api/v1/backtest/combos",
                       json={"slug": "x", "name": "X", "components": []}).status_code == 400
    assert client.post("/api/v1/backtest/combos",
                       json={"slug": "Bad Slug!", "name": "X",
                             "components": [{"module": "strategies.sma_cross", "weight": 1}]}).status_code == 400
