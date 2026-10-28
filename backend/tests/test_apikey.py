import pytest
from fastapi import HTTPException

from app.services.apikey_service import create_key, verify_key, hash_key
from app.deps.auth import require_scope


def test_create_key_stores_hash_not_plaintext(db_session):
    plaintext, row = create_key(db_session, "bot-1", "paper:write")
    assert plaintext.startswith("ith_")
    assert row.key_hash == hash_key(plaintext)
    assert row.key_hash != plaintext
    assert row.key_prefix == plaintext[:10]


def test_verify_key_roundtrip(db_session):
    plaintext, row = create_key(db_session, "bot-2", "paper:write")
    found = verify_key(db_session, plaintext)
    assert found is not None and found.id == row.id
    assert found.last_used_at is not None
    assert verify_key(db_session, "ith_wrongkey") is None


def test_inactive_key_is_rejected(db_session):
    plaintext, row = create_key(db_session, "bot-3", "paper:write")
    row.is_active = False
    db_session.commit()
    assert verify_key(db_session, plaintext) is None


def test_require_scope(db_session):
    _, row = create_key(db_session, "bot-4", "paper:write,read")
    require_scope(row, "paper:write")  # no raise
    require_scope(row, "read")
    with pytest.raises(HTTPException) as exc:
        require_scope(row, "real:write")
    assert exc.value.status_code == 403
