"""FastAPI auth dependencies for API-key-protected (bot/MCP) endpoints."""
import os
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiKey
from app.services.apikey_service import verify_key


def get_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> ApiKey:
    """Authenticate via `X-API-Key: <key>` or `Authorization: Bearer <key>`."""
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing API key")
    key = verify_key(db, token)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key


def require_scope(key: ApiKey, scope: str) -> None:
    """Raise 403 unless the key carries `scope` (CSV in key.scopes)."""
    scopes = {s.strip() for s in (key.scopes or "").split(",") if s.strip()}
    if scope not in scopes:
        raise HTTPException(status_code=403, detail=f"API key missing scope: {scope}")


# --- Per-key sliding-window rate limiter (in-memory) ---------------------------
_RATE_WINDOW_SEC = 1.0
_RATE_MAX = int(os.getenv("BOT_RATE_MAX_PER_SEC", "10"))
_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(key: ApiKey) -> None:
    """Allow at most _RATE_MAX requests per key per _RATE_WINDOW_SEC; else 429.

    Keyed by key_hash (stable + unique) so test DBs that reuse integer ids do
    not cross-contaminate buckets.
    """
    now = time.monotonic()
    bucket = _hits[key.key_hash]
    cutoff = now - _RATE_WINDOW_SEC
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _RATE_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    bucket.append(now)


def get_rate_limited_api_key(key: ApiKey = Depends(get_api_key)) -> ApiKey:
    """Authenticate + apply the per-key rate limit. Use on write endpoints."""
    rate_limit(key)
    return key
