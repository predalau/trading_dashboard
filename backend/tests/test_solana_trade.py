from app.main import app
from app.api.solana_trade import get_jupiter, get_solana

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


class FakeJup:
    async def get_quote(self, i, o, amount, slippage_bps=50):
        return {"inAmount": str(amount), "outAmount": "1024606", "priceImpactPct": "0", "slippageBps": slippage_bps}

    async def build_swap_tx(self, quote, user_pubkey, wrap_unwrap_sol=True):
        return {"swap_transaction": "UNSIGNED_B64", "last_valid_block_height": 123}


class FakeSolana:
    def __init__(self, status="confirmed"):
        self.status = status

    async def send_transaction(self, signed_b64):
        return "SIG123"

    async def get_signature_status(self, sig):
        return self.status


def test_quote(client):
    app.dependency_overrides[get_jupiter] = lambda: FakeJup()
    try:
        r = client.post("/api/v1/solana/quote", json={"input_mint": SOL, "output_mint": USDC, "amount": 10_000_000})
        assert r.status_code == 200, r.text
        assert r.json()["out_amount"] == "1024606"
    finally:
        app.dependency_overrides.pop(get_jupiter, None)


def test_prepare_returns_unsigned_tx(client):
    app.dependency_overrides[get_jupiter] = lambda: FakeJup()
    try:
        r = client.post("/api/v1/solana/swap/prepare", json={
            "input_mint": SOL, "output_mint": USDC, "amount": 10_000_000, "user_pubkey": "PubKey1"})
        assert r.status_code == 200, r.text
        assert r.json()["swap_transaction"] == "UNSIGNED_B64"
    finally:
        app.dependency_overrides.pop(get_jupiter, None)


def test_submit_records_order(client, db_session):
    app.dependency_overrides[get_solana] = lambda: FakeSolana("confirmed")
    try:
        r = client.post("/api/v1/solana/swap/submit", json={
            "signed_transaction": "SIGNED_B64", "input_mint": SOL, "output_mint": USDC, "in_amount": 0.01})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["signature"] == "SIG123"
        assert body["status"] == "confirmed"
        assert "solscan.io/tx/SIG123" in body["explorer"]
        from app.models import Order
        o = db_session.query(Order).filter(Order.id == body["order_id"]).first()
        assert o.mode == "solana" and o.tx_signature == "SIG123" and o.status.value == "FILLED"
    finally:
        app.dependency_overrides.pop(get_solana, None)


def test_submit_failed_tx_marks_cancelled(client):
    app.dependency_overrides[get_solana] = lambda: FakeSolana("failed")
    try:
        r = client.post("/api/v1/solana/swap/submit", json={
            "signed_transaction": "SIGNED_B64", "input_mint": SOL, "output_mint": USDC})
        assert r.status_code == 200
        assert r.json()["status"] == "failed"
    finally:
        app.dependency_overrides.pop(get_solana, None)
