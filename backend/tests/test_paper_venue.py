import pytest

from app.execution.base import OrderRequest
from app.execution.paper import PaperVenue
from app.services.account_service import get_or_create_default_account
from app.services.paper_accounting import InsufficientBalance
from app.models import Order, Trade


async def test_paper_market_order_fills_and_debits(db_session):
    acct = get_or_create_default_account(db_session)
    start = acct.available_balance
    req = OrderRequest(
        mode="paper", symbol="SOLUSDT", side="BUY", type="MARKET",
        quantity=2, price=100, client_order_id="c1", api_key_id=1,
    )
    res = await PaperVenue().place_order(db_session, req, acct)
    assert res.status == "FILLED"
    assert res.filled_price == 100
    assert res.trade_id is not None
    assert res.idempotent_replay is False
    db_session.refresh(acct)
    assert acct.available_balance == start - 200
    assert db_session.query(Trade).count() == 1
    assert db_session.query(Order).count() == 1


async def test_paper_order_is_idempotent(db_session):
    acct = get_or_create_default_account(db_session)
    req = OrderRequest(
        mode="paper", symbol="SOLUSDT", side="BUY",
        quantity=1, price=50, client_order_id="dup", api_key_id=7,
    )
    await PaperVenue().place_order(db_session, req, acct)
    r2 = await PaperVenue().place_order(db_session, req, acct)
    assert r2.idempotent_replay is True
    assert db_session.query(Order).count() == 1
    assert db_session.query(Trade).count() == 1


async def test_insufficient_balance_raises(db_session):
    acct = get_or_create_default_account(db_session)
    req = OrderRequest(mode="paper", symbol="SOLUSDT", side="BUY", quantity=1000, price=1_000_000_000)
    with pytest.raises(InsufficientBalance):
        await PaperVenue().place_order(db_session, req, acct)
