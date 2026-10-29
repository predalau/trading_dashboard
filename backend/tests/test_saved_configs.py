def _payload(**over):
    p = {"name": "RSI fast", "module": "strategies.rsi", "params": {"period": 7},
         "symbol": "BTCUSDT", "timeframe": "1h", "lookback": 500,
         "bias": {"enabled": True, "entry_threshold": 0.5}}
    p.update(over)
    return p


def test_save_list_overwrite_delete(client):
    r = client.post("/api/v1/backtest/saved-configs", json=_payload())
    assert r.status_code == 200, r.text
    body = r.json()
    cid = body["id"]
    assert body["slug"] == "rsi" and body["params"]["period"] == 7

    assert any(c["id"] == cid for c in client.get("/api/v1/backtest/saved-configs").json())

    # same name -> upsert in place
    r2 = client.post("/api/v1/backtest/saved-configs", json=_payload(params={"period": 21}))
    assert r2.json()["id"] == cid
    assert r2.json()["params"]["period"] == 21

    assert client.delete(f"/api/v1/backtest/saved-configs/{cid}").status_code == 200
    assert client.get("/api/v1/backtest/saved-configs").json() == []


def test_save_rejects_bad_module(client):
    r = client.post("/api/v1/backtest/saved-configs", json=_payload(name="bad", module="strategies.nope"))
    assert r.status_code == 400


def test_save_requires_name(client):
    r = client.post("/api/v1/backtest/saved-configs", json=_payload(name="   "))
    assert r.status_code == 400
