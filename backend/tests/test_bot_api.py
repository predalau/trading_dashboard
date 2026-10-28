from app.services.apikey_service import create_key
from app.models import Order


def _key(db, scopes="paper:write", label="bot"):
    plaintext, row = create_key(db, label, scopes)
    return plaintext


def test_no_key_is_401(client):
    r = client.post("/api/v1/bot/orders", json={"symbol": "SOLUSDT", "side": "BUY", "quantity": 1, "price": 100})
    assert r.status_code == 401


def test_paper_order_succeeds_and_persists(client, db_session):
    k = _key(db_session, "paper:write")
    r = client.post(
        "/api/v1/bot/orders",
        headers={"X-API-Key": k},
        json={"mode": "paper", "symbol": "SOLUSDT", "side": "BUY", "quantity": 2, "price": 100},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "FILLED"
    assert body["filled_price"] == 100
    assert db_session.query(Order).count() == 1


def test_paper_key_cannot_trade_solana_403(client, db_session):
    k = _key(db_session, "paper:write")
    r = client.post(
        "/api/v1/bot/orders",
        headers={"X-API-Key": k},
        json={"mode": "solana", "symbol": "SOL", "side": "BUY", "quantity": 1, "price": 100},
    )
    assert r.status_code == 403


def test_real_scope_solana_is_400_not_implemented(client, db_session):
    # Scope passes, but the solana venue is not wired yet (Phase 4).
    k = _key(db_session, "real:write")
    r = client.post(
        "/api/v1/bot/orders",
        headers={"X-API-Key": k},
        json={"mode": "solana", "symbol": "SOL", "side": "BUY", "quantity": 1, "price": 100},
    )
    assert r.status_code == 400


def test_idempotent_client_order_id(client, db_session):
    k = _key(db_session, "paper:write")
    payload = {"mode": "paper", "symbol": "SOLUSDT", "side": "BUY", "quantity": 1, "price": 50, "client_order_id": "abc"}
    r1 = client.post("/api/v1/bot/orders", headers={"X-API-Key": k}, json=payload)
    r2 = client.post("/api/v1/bot/orders", headers={"X-API-Key": k}, json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["idempotent_replay"] is True
    assert r1.json()["order_id"] == r2.json()["order_id"]
    assert db_session.query(Order).count() == 1


def test_list_orders_scoped_to_key(client, db_session):
    k = _key(db_session, "paper:write")
    client.post("/api/v1/bot/orders", headers={"X-API-Key": k},
                json={"mode": "paper", "symbol": "SOLUSDT", "side": "BUY", "quantity": 1, "price": 50})
    r = client.get("/api/v1/bot/orders", headers={"X-API-Key": k})
    assert r.status_code == 200
    assert len(r.json()) == 1
