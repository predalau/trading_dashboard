"""Opt-in encrypted bot hot wallet for unattended Solana bots.

SAFETY MODEL (all enforced here):
  * DISABLED by default — no config row, or enabled=False, means every trade is
    refused.
  * Token allowlist starts EMPTY = deny-all. A swap's OUTPUT mint must be
    explicitly allowlisted by the operator.
  * Per-day USD cap (default $10) across all hot-wallet swaps.
  * The secret key is stored Fernet-encrypted (WALLET_ENC_KEY from the
    environment / a Docker secret, never committed) and decrypted in-memory only
    at signing time.

This module is NOT wired into the live order path by default. Enabling it
requires: a funded throwaway wallet, WALLET_ENC_KEY set, a populated allowlist,
enabled=True, and explicit operator sign-off.
"""
import datetime
import os
from typing import Optional

from sqlalchemy.orm import Session

from app.models import BotHotWallet, BotWalletSpend


class HotWalletError(Exception):
    pass


class HotWalletDisabled(HotWalletError):
    pass


class TradeNotAllowed(HotWalletError):
    pass


def _fernet():
    from cryptography.fernet import Fernet
    key = os.getenv("WALLET_ENC_KEY")
    if not key:
        raise HotWalletError("WALLET_ENC_KEY is not set")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_secret(plaintext_secret: str) -> str:
    return _fernet().encrypt(plaintext_secret.encode()).decode()


def decrypt_secret(cfg: BotHotWallet) -> bytes:
    if not cfg or not cfg.encrypted_secret:
        raise HotWalletError("no encrypted secret configured")
    return _fernet().decrypt(cfg.encrypted_secret.encode())


def get_config(db: Session) -> Optional[BotHotWallet]:
    return db.query(BotHotWallet).first()


def is_enabled(db: Session) -> bool:
    cfg = get_config(db)
    return bool(cfg and cfg.enabled)


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def spent_today_usd(db: Session, day: Optional[str] = None) -> float:
    row = db.query(BotWalletSpend).filter(BotWalletSpend.day == (day or _today())).first()
    return row.usd_spent if row else 0.0


def check_trade(db: Session, output_mint: str, usd_value: float) -> None:
    """Raise if the trade is not permitted. Order of checks: enabled, allowlist, cap."""
    cfg = get_config(db)
    if not cfg or not cfg.enabled:
        raise HotWalletDisabled("bot hot wallet is disabled")
    allow = set(cfg.token_allowlist or [])
    if output_mint not in allow:          # empty allowlist => deny-all
        raise TradeNotAllowed(f"output token not in allowlist: {output_mint}")
    if usd_value <= 0:
        raise TradeNotAllowed("usd_value must be positive")
    cap = cfg.max_usd_per_day
    if spent_today_usd(db) + usd_value > cap + 1e-9:
        raise TradeNotAllowed(
            f"daily cap ${cap:.2f} would be exceeded "
            f"(spent ${spent_today_usd(db):.2f} + ${usd_value:.2f})"
        )


def record_spend(db: Session, usd_value: float, day: Optional[str] = None) -> None:
    day = day or _today()
    row = db.query(BotWalletSpend).filter(BotWalletSpend.day == day).first()
    if row:
        row.usd_spent += usd_value
    else:
        db.add(BotWalletSpend(day=day, usd_spent=usd_value))
    db.commit()


async def sign_and_send(db: Session, unsigned_tx_b64: str, output_mint: str,
                        usd_value: float, solana) -> str:
    """Guardrail-checked server-side sign + broadcast. Enabling path only.

    `solana` is a SolanaService (for send_transaction). Requires solders.
    """
    check_trade(db, output_mint, usd_value)  # raises if not permitted
    secret = decrypt_secret(get_config(db))
    try:
        import base64
        from solders.keypair import Keypair
        from solders.transaction import VersionedTransaction
    except ImportError:
        raise HotWalletError("server-side signing deps (solders) not installed")

    keypair = Keypair.from_bytes(secret)
    raw = base64.b64decode(unsigned_tx_b64)
    unsigned = VersionedTransaction.from_bytes(raw)
    signed = VersionedTransaction(unsigned.message, [keypair])
    signed_b64 = base64.b64encode(bytes(signed)).decode()

    signature = await solana.send_transaction(signed_b64)
    record_spend(db, usd_value)
    return signature
