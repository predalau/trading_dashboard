"""Read-only Solana balances via JSON-RPC (no private key required).

Fetches native SOL + SPL token balances for an address. An httpx client can be
injected for tests (httpx.MockTransport); otherwise a client is created per call.
"""
import os
from typing import Optional

import httpx

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SOL_MINT = "So11111111111111111111111111111111111111112"  # wrapped SOL mint (for pricing)
LAMPORTS_PER_SOL = 1_000_000_000


class SolanaService:
    def __init__(self, rpc_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self._client = client

    async def _rpc(self, method: str, params: list) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        if self._client is not None:
            resp = await self._client.post(self.rpc_url, json=payload)
            return resp.json()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(self.rpc_url, json=payload)
            return resp.json()

    async def get_sol_balance(self, address: str) -> float:
        data = await self._rpc("getBalance", [address])
        lamports = data["result"]["value"]
        return lamports / LAMPORTS_PER_SOL

    async def get_token_balances(self, address: str) -> list[dict]:
        params = [address, {"programId": TOKEN_PROGRAM_ID}, {"encoding": "jsonParsed"}]
        data = await self._rpc("getTokenAccountsByOwner", params)
        out: list[dict] = []
        for acc in data["result"]["value"]:
            info = acc["account"]["data"]["parsed"]["info"]
            amount = info["tokenAmount"]
            ui = amount.get("uiAmount")
            if ui and ui > 0:
                out.append({"mint": info["mint"], "amount": float(ui), "decimals": amount["decimals"]})
        return out

    async def get_wallet_balances(self, address: str) -> dict:
        sol = await self.get_sol_balance(address)
        tokens = await self.get_token_balances(address)
        return {"address": address, "sol": sol, "tokens": tokens}

    async def send_transaction(self, signed_b64: str) -> str:
        """Broadcast a client-signed, base64-serialized transaction. Returns the signature."""
        data = await self._rpc("sendTransaction", [
            signed_b64, {"encoding": "base64", "skipPreflight": False, "maxRetries": 3},
        ])
        if data.get("error"):
            raise RuntimeError(data["error"].get("message", "sendTransaction failed"))
        return data["result"]

    async def get_signature_status(self, signature: str) -> Optional[str]:
        """Return 'processed'|'confirmed'|'finalized'|'failed', or None if unknown yet."""
        data = await self._rpc("getSignatureStatuses", [[signature], {"searchTransactionHistory": True}])
        values = (data.get("result") or {}).get("value") or [None]
        val = values[0]
        if not val:
            return None
        if val.get("err"):
            return "failed"
        return val.get("confirmationStatus")
