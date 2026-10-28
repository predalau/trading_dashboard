"""API key generation and verification for bot/MCP authentication.

Keys look like 'ith_<urlsafe>'. Only the sha256 hash is stored; the plaintext
is returned exactly once at creation time.
"""
import hashlib
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import ApiKey

KEY_PREFIX = "ith_"


def hash_key(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode()).hexdigest()


def create_key(db: Session, label: str, scopes: str = "paper:write") -> tuple[str, ApiKey]:
    """Create a key. Returns (plaintext_shown_once, row)."""
    plaintext = f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"
    row = ApiKey(
        label=label,
        key_prefix=plaintext[:10],
        key_hash=hash_key(plaintext),
        scopes=scopes,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return plaintext, row


def verify_key(db: Session, plaintext: str) -> ApiKey | None:
    """Return the active ApiKey matching plaintext, updating last_used_at."""
    row = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == hash_key(plaintext), ApiKey.is_active.is_(True))
        .first()
    )
    if row:
        row.last_used_at = datetime.utcnow()
        db.commit()
    return row
