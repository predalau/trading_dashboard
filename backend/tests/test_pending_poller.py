from app.main import app
from app.api.trades import get_market
from app.models import Trade
from app.services.account_service import get_or_create_default_account
from app.services.pending_orders import process_pending_orders


class FakeMarket:
    def __init__(self, prices):
        self.prices = prices

    async def get_price(self, symbol):
        return {"price": self.prices[symbol]}


def _mk_pending(db, acct, symbol, entry, trigger_above, qty):
    t = Trade(account_id=acct.id, symbol=symbol, exchange="BINANCE", trade_type="BUY",
              entry_price=entry, quantity=qty, is_open=False, status="pending",
              trigger_above=trigger_above)
    db.add(t)
    db.flush()
    return t


async def test_process_pending_fills_cancels_and_skips(db_session):
    acct = get_or_create_default_account(db_session)
    reached = _mk_pending(db_session, acct, "BTCUSDT", 100.0, False, 1.0)       # price 95 <= 100 -> fill
    not_reached = _mk_pending(db_session, acct, "ETHUSDT", 50.0, True, 1.0)     # price 40 < 50 -> skip
    too_big = _mk_pending(db_session, acct, "BTCUSDT", 100.0, False, 1_000_000) # cost > balance -> cancel
    db_session.commit()

    res = await process_pending_orders(db_session, FakeMarket({"BTCUSDT": 95.0, "ETHUSDT": 40.0}))

    assert reached.id in res["filled"]
    assert too_big.id in res["cancelled"]
    assert not_reached.id not in res["filled"] and not_reached.id not in res["cancelled"]

    db_session.refresh(reached); db_session.refresh(not_reached); db_session.refresh(too_big)
    assert reached.status == "open" and reached.is_open is True
    assert not_reached.status == "pending"
    assert too_big.status == "cancelled"


def test_process_pending_endpoint(client, db_session):
    acct = get_or_create_default_account(db_session)
    _mk_pending(db_session, acct, "BTCUSDT", 100.0, False, 1.0)
    db_session.commit()
    app.dependency_overrides[get_market] = lambda: FakeMarket({"BTCUSDT": 90.0})
    try:
        r = client.post("/api/v1/trades/process-pending")
    finally:
        app.dependency_overrides.pop(get_market, None)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["checked"] == 1 and len(body["filled"]) == 1
