import pytest

from app.models import Wallet
from app.services.account_service import get_or_create_default_account
from app.services.paper_accounting import open_paper_position
from app.services.portfolio_service import build_summary
from app.services.solana_service import SOL_MINT


class FakeMarket:
    async def get_price(self, symbol):
        return {"price": 110.0}


class FakeSolana:
    async def get_wallet_balances(self, address):
        return {"address": address, "sol": 2.0,
                "tokens": [{"mint": "USDCMINT", "amount": 50.0, "decimals": 6}]}


class FakePricing:
    async def get_prices(self, mints):
        return {SOL_MINT: 150.0, "USDCMINT": 1.0}


async def test_summary_combines_paper_and_wallet(db_session):
    acct = get_or_create_default_account(db_session)
    open_paper_position(db_session, acct, symbol="SOLUSDT", side="BUY", quantity=2, price=100)
    db_session.commit()
    db_session.add(Wallet(chain="solana", address="addr", label="w"))
    db_session.commit()

    s = await build_summary(db_session, solana=FakeSolana(), pricing=FakePricing(), market=FakeMarket())

    # entry 100 x2 = cost 200; mark 110 -> unrealized +20; equity = 100000 + 20
    assert s["paper"]["unrealized_pl"] == pytest.approx(20.0)
    assert s["paper"]["equity"] == pytest.approx(100020.0)
    # wallet: 2 SOL * 150 + 50 USDC * 1 = 350
    assert s["wallets_total_usd"] == pytest.approx(350.0)
    assert s["grand_total_usd"] == pytest.approx(100370.0)


async def test_summary_no_wallets_is_paper_only(db_session):
    get_or_create_default_account(db_session)
    s = await build_summary(db_session, solana=FakeSolana(), pricing=FakePricing(), market=FakeMarket())
    assert s["wallets"] == []
    assert s["wallets_total_usd"] == 0.0
    assert s["grand_total_usd"] == pytest.approx(s["paper"]["equity"])
