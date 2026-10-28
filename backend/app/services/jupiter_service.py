"""Jupiter swap integration — quotes + unsigned transaction building.

This service NEVER signs or sends transactions. It prepares an unsigned,
base64-encoded versioned transaction that the caller (browser wallet, or the
gated hot-wallet service) signs. Injectable httpx client for tests.
"""
import os
from typing import Optional

import httpx

JUPITER_SWAP_URL = os.getenv("JUPITER_SWAP_URL", "https://lite-api.jup.ag/swap/v1")


class JupiterError(Exception):
    pass


class JupiterService:
    def __init__(self, base_url: Optional[str] = None, client: Optional[httpx.AsyncClient] = None):
        self.base = (base_url or JUPITER_SWAP_URL).rstrip("/")
        self._client = client

    async def _get(self, path: str, params: dict) -> httpx.Response:
        if self._client is not None:
            return await self._client.get(f"{self.base}{path}", params=params)
        async with httpx.AsyncClient(timeout=25) as c:
            return await c.get(f"{self.base}{path}", params=params)

    async def _post(self, path: str, json: dict) -> httpx.Response:
        if self._client is not None:
            return await self._client.post(f"{self.base}{path}", json=json)
        async with httpx.AsyncClient(timeout=25) as c:
            return await c.post(f"{self.base}{path}", json=json)

    async def get_quote(self, input_mint: str, output_mint: str, amount: int,
                        slippage_bps: int = 50) -> dict:
        """Quote a swap of `amount` (in input_mint base units) -> output_mint."""
        if int(amount) <= 0:
            raise JupiterError("amount must be positive")
        r = await self._get("/quote", {
            "inputMint": input_mint, "outputMint": output_mint,
            "amount": int(amount), "slippageBps": int(slippage_bps),
        })
        if r.status_code >= 400:
            raise JupiterError(f"quote failed: HTTP {r.status_code}: {r.text[:200]}")
        return r.json()

    async def build_swap_tx(self, quote: dict, user_pubkey: str,
                            wrap_unwrap_sol: bool = True) -> dict:
        """Build an UNSIGNED base64 versioned transaction for `quote`."""
        r = await self._post("/swap", {
            "quoteResponse": quote, "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": wrap_unwrap_sol,
        })
        if r.status_code >= 400:
            raise JupiterError(f"swap build failed: HTTP {r.status_code}: {r.text[:200]}")
        d = r.json()
        if d.get("simulationError"):
            raise JupiterError(f"swap simulation error: {d['simulationError']}")
        if not d.get("swapTransaction"):
            raise JupiterError("no swapTransaction in Jupiter response")
        return {
            "swap_transaction": d["swapTransaction"],
            "last_valid_block_height": d.get("lastValidBlockHeight"),
        }
