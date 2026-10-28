"""FastAPI auth dependencies for API-key-protected (bot/MCP) endpoints."""
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
