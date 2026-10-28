def test_post_trade_autocreates_account_and_succeeds(client):
    resp = client.post(
        "/api/v1/trades/",
        json={
            "symbol": "BTCUSDT",
            "trade_type": "BUY",
            "entry_price": 50000,
            "quantity": 0.1,
            "stop_loss": 49000,
            "take_profit": 52000,
            "notes": "test",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["symbol"] == "BTCUSDT"
    assert body["is_open"] is True
    assert body["id"] is not None


def test_post_trade_short_side(client):
    resp = client.post(
        "/api/v1/trades/",
        json={"symbol": "SOLUSDT", "trade_type": "SELL", "entry_price": 150, "quantity": 2},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["trade_type"] == "SELL"
