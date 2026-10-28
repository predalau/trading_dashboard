"""USD pricing for Solana tokens via Jupiter Price API, with a process TTL cache.

An httpx client can be injected for tests; otherwise one is created per call.
Unknown/illiquid mints resolve to 0.0 rather than raising.
"""
import os
import time
from typing import Iterable, Optional

import httpx

JUPITER_PRICE_URL = os.getenv("JUPITER_PRICE_URL", "https://lite-api.jup.ag/price/v3")
_TTL_SEC = 60.0
_BATCH = 50  # Jupiter caps ids per call; also keeps the query string under URL limits
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
        seen: set[str] = set()
        for mint in mints:  # preserve caller order (e.g. SOL first) across batches
            if mint in seen:
                continue
            seen.add(mint)
            cached = _CACHE.get(mint)
            if cached and now - cached[0] < _TTL_SEC:
                result[mint] = cached[1]
            else:
                missing.append(mint)
        if missing:
            for i in range(0, len(missing), _BATCH):
                batch = missing[i:i + _BATCH]
                # Jupiter Price v3 returns {mint: {"usdPrice": <float>, ...}}.
                data = await self._fetch(batch) or {}
                for mint in batch:
                    entry = data.get(mint)
                    usd = entry.get("usdPrice") if entry else None
                    price = float(usd) if usd is not None else 0.0
                    _CACHE[mint] = (now, price)
                    result[mint] = price
        return result
