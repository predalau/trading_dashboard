from app.services.account_service import get_or_create_default_account


def test_list_accounts_returns_default(client, db_session):
    # Bootstrap a default account, then list via the API.
    get_or_create_default_account(db_session)
    resp = client.get("/api/v1/paper-trading/accounts")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["account_name"]
    assert body[0]["available_balance"] == body[0]["initial_balance"]


def test_list_accounts_empty(client):
    resp = client.get("/api/v1/paper-trading/accounts")
    assert resp.status_code == 200
    assert resp.json() == []
