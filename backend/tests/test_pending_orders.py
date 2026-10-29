from app.main import app
from app.api.trades import get_market
from app.models import Trade
from app.services.account_service import get_or_create_default_account


class FakeMarket:
    def __init__(self, price):
        self.price = price

    async def get_price(self, symbol):
        return {"price": self.price}


def _avail(db):
    return get_or_create_default_account(db).available_balance


def test_pending_order_does_not_open_or_reserve(client, db_session):
    before = _avail(db_session)
    r = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 100.0,
        "quantity": 1.0, "pending": True, "reference_price": 110.0,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["is_open"] is False
    assert body["trigger_above"] is False  # entry 100 < ref 110 -> fills on price <= 100
    assert _avail(db_session) == before      # no margin reserved


def test_activate_when_price_reached_opens_and_reserves(client, db_session):
    before = _avail(db_session)
    oid = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 100.0,
        "quantity": 2.0, "pending": True, "reference_price": 110.0,
    }).json()["id"]

    app.dependency_overrides[get_market] = lambda: FakeMarket(99.0)  # dropped to entry
    try:
        r = client.post(f"/api/v1/trades/{oid}/activate")
    finally:
        app.dependency_overrides.pop(get_market, None)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "open" and r.json()["is_open"] is True
    assert _avail(db_session) == before - 100.0 * 2.0


def test_activate_when_not_reached_rejected(client, db_session):
    oid = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 100.0,
        "quantity": 1.0, "pending": True, "reference_price": 110.0,
    }).json()["id"]
    app.dependency_overrides[get_market] = lambda: FakeMarket(105.0)  # still above entry
    try:
        r = client.post(f"/api/v1/trades/{oid}/activate")
    finally:
        app.dependency_overrides.pop(get_market, None)
    assert r.status_code == 400
    assert db_session.query(Trade).get(oid).status == "pending"  # unchanged


def test_trigger_above_direction(client, db_session):
    # entry 120 > ref 110 -> trigger_above True (stop entry, fills on price >= 120)
    oid = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 120.0,
        "quantity": 1.0, "pending": True, "reference_price": 110.0,
    }).json()["id"]
    assert db_session.query(Trade).get(oid).trigger_above is True
    app.dependency_overrides[get_market] = lambda: FakeMarket(125.0)
    try:
        r = client.post(f"/api/v1/trades/{oid}/activate")
    finally:
        app.dependency_overrides.pop(get_market, None)
    assert r.status_code == 200 and r.json()["status"] == "open"


def test_cancel_pending_order_no_balance_change(client, db_session):
    before = _avail(db_session)
    oid = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 100.0,
        "quantity": 1.0, "pending": True, "reference_price": 110.0,
    }).json()["id"]
    r = client.request("DELETE", f"/api/v1/trades/{oid}")
    assert r.status_code == 200
    assert db_session.query(Trade).get(oid).status == "cancelled"
    assert _avail(db_session) == before
