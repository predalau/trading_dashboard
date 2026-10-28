import app.deps.auth as auth
from app.services.apikey_service import create_key


def test_burst_over_limit_returns_429(client, db_session, monkeypatch):
    monkeypatch.setattr(auth, "_RATE_MAX", 2)
    plaintext, _ = create_key(db_session, "rl", "paper:write")
    payload = {"mode": "paper", "symbol": "SOLUSDT", "side": "BUY", "quantity": 1, "price": 10}
    codes = [
        client.post("/api/v1/bot/orders", headers={"X-API-Key": plaintext}, json=payload).status_code
        for _ in range(3)
    ]
    assert codes[:2] == [200, 200]
    assert codes[2] == 429
