"""USD pricing for Solana tokens via Jupiter Price API, with a process TTL cache.

An httpx client can be injected for tests; otherwise one is created per call.
Unknown/illiquid mints resolve to 0.0 rather than raising.
"""
import os
import time
from typing import Iterable, Optional

import httpx

JUPITER_PRICE_URL = os.getenv("JUPITER_PRICE_URL", "https://api.jup.ag/price/v2")
_TTL_SEC = 60.0
_CACHE: dict[str, tuple[float, float]] = {}  # mint -> (fetched_at, price)


def clear_cache() -> None:
    _CACHE.clear()


class PricingService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None, url: Optional[str] = None):
        self._client = client
        self.url = url or JUPITER_PRICE_URL

    async def _fetch(self, mints: list[str]) -> dict:
        params = {"ids": ",".join(mints)}
        if self._client is not None:
            resp = await self._client.get(self.url, params=params)
            return resp.json()
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(self.url, params=params)
            return resp.json()

    async def get_prices(self, mints: Iterable[str]) -> dict[str, float]:
        now = time.time()
        result: dict[str, float] = {}
        missing: list[str] = []
        for mint in set(mints):
            cached = _CACHE.get(mint)
            if cached and now - cached[0] < _TTL_SEC:
                result[mint] = cached[1]
            else:
                missing.append(mint)
        if missing:
            data = (await self._fetch(missing)).get("data", {}) or {}
            for mint in missing:
                entry = data.get(mint)
                price = float(entry["price"]) if entry and entry.get("price") else 0.0
                _CACHE[mint] = (now, price)
                result[mint] = price
        return result
