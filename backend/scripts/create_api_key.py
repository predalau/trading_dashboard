"""Mint a bot/MCP API key.

Usage (inside the backend container):
    python -m scripts.create_api_key "my-bot" paper:write
    python -m scripts.create_api_key "my-bot" "paper:write,read"

Prints the plaintext key ONCE. Store it now; only its hash is kept.
"""
import logging
import sys

logging.disable(logging.CRITICAL)  # silence SQLAlchemy echo so stdout is just the key

from app.database import SessionLocal  # noqa: E402
from app.services.apikey_service import create_key  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m scripts.create_api_key <label> [scopes]", file=sys.stderr)
        raise SystemExit(2)
    label = sys.argv[1]
    scopes = sys.argv[2] if len(sys.argv) > 2 else "paper:write"
    db = SessionLocal()
    try:
        plaintext, row = create_key(db, label, scopes)
    finally:
        db.close()
    print(plaintext)
    print(f"# id={row.id} label={row.label!r} scopes={row.scopes!r} prefix={row.key_prefix}", file=sys.stderr)


if __name__ == "__main__":
    main()
