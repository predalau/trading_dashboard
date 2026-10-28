from app.services.account_service import get_or_create_default_account


def test_bootstrap_creates_user_and_account(db_session):
    account = get_or_create_default_account(db_session)
    assert account.id is not None
    assert account.available_balance == account.initial_balance
    assert account.current_balance == account.initial_balance


def test_bootstrap_is_idempotent(db_session):
    first = get_or_create_default_account(db_session)
    second = get_or_create_default_account(db_session)
    assert first.id == second.id
