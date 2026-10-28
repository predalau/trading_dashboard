"""Bootstrap and lookup for the single operator's default user + paper account.

The frontend's trade path (POST /api/v1/trades/) and the paper trading venue
operate against a default account. On a fresh database there is no user or
account, which previously caused POST /api/v1/trades/ to 400. These helpers
lazily create and return the defaults, and are called at app startup.
"""
import os

from sqlalchemy.orm import Session

from app.models import PaperTradingAccount, User

DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "preda")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "preda@localhost")
DEFAULT_ACCOUNT_NAME = os.getenv("DEFAULT_ACCOUNT_NAME", "main")
PAPER_STARTING_BALANCE = float(os.getenv("PAPER_STARTING_BALANCE", "100000"))


def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).filter(User.username == DEFAULT_USERNAME).first()
    if user:
        return user
    user = User(username=DEFAULT_USERNAME, email=DEFAULT_EMAIL)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_default_account(db: Session) -> PaperTradingAccount:
    account = (
        db.query(PaperTradingAccount).order_by(PaperTradingAccount.id).first()
    )
    if account:
        return account
    user = get_or_create_default_user(db)
    account = PaperTradingAccount(
        user_id=user.id,
        account_name=DEFAULT_ACCOUNT_NAME,
        initial_balance=PAPER_STARTING_BALANCE,
        current_balance=PAPER_STARTING_BALANCE,
        available_balance=PAPER_STARTING_BALANCE,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
