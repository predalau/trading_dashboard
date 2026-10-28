import pytest

from app.models import PaperTradingAccount


def _balance(db):
    return db.query(PaperTradingAccount).first()


def test_open_reserves_margin_and_close_realizes_pnl(client, db_session):
    # Open LONG: entry 100, qty 2 -> cost 200
    r = client.post(
        "/api/v1/trades/",
        json={"symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 100, "quantity": 2},
    )
    assert r.status_code == 200, r.text
    acct = _balance(db_session)
    start = acct.initial_balance
    assert acct.available_balance == pytest.approx(start - 200)
    assert acct.current_balance == pytest.approx(start)  # equity flat on open

    tid = r.json()["id"]
    # Close at 110 -> P&L +20
    r2 = client.request("DELETE", f"/api/v1/trades/{tid}", json={"exit_price": 110})
    assert r2.status_code == 200, r2.text
    assert r2.json()["profit_loss"] == pytest.approx(20.0)
    db_session.refresh(acct)
    assert acct.available_balance == pytest.approx(start + 20)
    assert acct.current_balance == pytest.approx(start + 20)


def test_short_close_realizes_pnl(client, db_session):
    r = client.post(
        "/api/v1/trades/",
        json={"symbol": "SOLUSDT", "trade_type": "SELL", "entry_price": 100, "quantity": 2},
    )
    tid = r.json()["id"]
    acct = _balance(db_session)
    start = acct.initial_balance
    # Close short at 90 -> profit +20
    r2 = client.request("DELETE", f"/api/v1/trades/{tid}", json={"exit_price": 90})
    assert r2.json()["profit_loss"] == pytest.approx(20.0)
    db_session.refresh(acct)
    assert acct.available_balance == pytest.approx(start + 20)


def test_insufficient_balance_rejected(client, db_session):
    r = client.post(
        "/api/v1/trades/",
        json={"symbol": "BTCUSDT", "trade_type": "BUY", "entry_price": 1_000_000_000, "quantity": 1000},
    )
    assert r.status_code == 400
    assert "Insufficient" in r.json()["detail"]
