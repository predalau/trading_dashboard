import os

import pytest

from app.models import BotHotWallet, BotWalletSpend
from app.services import hotwallet_service as hw

MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _enable(db, allowlist=None, cap=10.0):
    cfg = BotHotWallet(enabled=True, max_usd_per_day=cap, token_allowlist=allowlist or [])
    db.add(cfg)
    db.commit()
    return cfg


def test_disabled_by_default_denies(db_session):
    # no config row at all
    with pytest.raises(hw.HotWalletDisabled):
        hw.check_trade(db_session, MINT, 1.0)


def test_enabled_empty_allowlist_is_deny_all(db_session):
    _enable(db_session, allowlist=[])
    with pytest.raises(hw.TradeNotAllowed):
        hw.check_trade(db_session, MINT, 1.0)


def test_allowlisted_under_cap_passes(db_session):
    _enable(db_session, allowlist=[MINT], cap=10.0)
    hw.check_trade(db_session, MINT, 5.0)  # no raise


def test_daily_cap_enforced(db_session):
    _enable(db_session, allowlist=[MINT], cap=10.0)
    hw.record_spend(db_session, 8.0)
    with pytest.raises(hw.TradeNotAllowed):
        hw.check_trade(db_session, MINT, 5.0)  # 8 + 5 > 10
    hw.check_trade(db_session, MINT, 2.0)      # 8 + 2 == 10 ok


def test_non_allowlisted_token_rejected_even_under_cap(db_session):
    _enable(db_session, allowlist=[MINT], cap=10.0)
    with pytest.raises(hw.TradeNotAllowed):
        hw.check_trade(db_session, "SomeOtherMint", 1.0)


def test_fernet_roundtrip(monkeypatch):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("WALLET_ENC_KEY", key)
    ct = hw.encrypt_secret("super-secret-key-bytes")
    cfg = BotHotWallet(encrypted_secret=ct)
    assert hw.decrypt_secret(cfg) == b"super-secret-key-bytes"


def test_encrypt_requires_key(monkeypatch):
    monkeypatch.delenv("WALLET_ENC_KEY", raising=False)
    with pytest.raises(hw.HotWalletError):
        hw.encrypt_secret("x")
