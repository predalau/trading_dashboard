VALID_SOL = "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"  # a real-looking base58 addr


def test_add_and_list_wallet(client):
    r = client.post("/api/v1/wallets", json={"address": VALID_SOL, "label": "main"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["chain"] == "solana"
    assert body["is_watch_only"] is True

    r2 = client.get("/api/v1/wallets")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_invalid_address_rejected(client):
    r = client.post("/api/v1/wallets", json={"address": "not-an-address!"})
    assert r.status_code == 400


def test_duplicate_wallet_conflict(client):
    client.post("/api/v1/wallets", json={"address": VALID_SOL})
    r = client.post("/api/v1/wallets", json={"address": VALID_SOL})
    assert r.status_code == 409


def test_delete_wallet(client):
    wid = client.post("/api/v1/wallets", json={"address": VALID_SOL}).json()["id"]
    r = client.request("DELETE", f"/api/v1/wallets/{wid}")
    assert r.status_code == 200
    assert client.get("/api/v1/wallets").json() == []
