from app.models import StrategyDef
from app.services.ohlcv_service import upsert_ohlcv

STEP = 3_600_000  # 1h in ms
BASE = 1_700_000_000_000


def _seed_bars(db, symbol="BTCUSDT", timeframe="1h", n=40):
    # Oscillating series so SMA crossovers (and trades) occur.
    closes = []
    for i in range(n):
        closes.append(100 + (10 if (i // 5) % 2 else -10) + i * 0.5)
    bars = [{"ts": BASE + i * STEP, "open": c, "high": c + 1, "low": c - 1,
             "close": c, "volume": 1.0} for i, c in enumerate(closes)]
    upsert_ohlcv(db, symbol, timeframe, bars)
    return BASE, BASE + (n - 1) * STEP


def test_run_backtest_by_module(client, db_session):
    start, end = _seed_bars(db_session)
    r = client.post("/api/v1/backtest/run", json={
        "module": "strategies.sma_cross", "symbol": "BTCUSDT", "timeframe": "1h",
        "start_ms": start, "end_ms": end, "params": {"fast": 3, "slow": 5},
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "done"
    assert body["bars"] >= 2
    assert "total_return" in body["metrics"]

    # fetch it back with the equity curve
    got = client.get(f"/api/v1/backtest/{body['id']}")
    assert got.status_code == 200
    assert got.json()["equity_curve"]
    assert len(client.get("/api/v1/backtest").json()) == 1


def test_run_by_registered_slug(client, db_session):
    start, end = _seed_bars(db_session)
    db_session.add(StrategyDef(slug="sma", name="SMA", module="strategies.sma_cross",
                               params={"fast": 3, "slow": 5}))
    db_session.commit()
    r = client.post("/api/v1/backtest/run", json={
        "strategy_slug": "sma", "symbol": "BTCUSDT", "timeframe": "1h",
        "start_ms": start, "end_ms": end,
    })
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "done"
    assert client.get("/api/v1/backtest/strategies").json()[0]["slug"] == "sma"


def test_bad_timeframe_rejected(client, db_session):
    r = client.post("/api/v1/backtest/run", json={
        "module": "strategies.sma_cross", "symbol": "BTCUSDT", "timeframe": "99x",
        "start_ms": BASE, "end_ms": BASE + STEP,
    })
    assert r.status_code == 400
