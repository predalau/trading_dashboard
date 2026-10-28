import httpx
import pytest

from app.services.pricing_service import PricingService, clear_cache

MINT_A = "So11111111111111111111111111111111111111112"
MINT_B = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_cache()
    yield
    clear_cache()


class _CountingHandler:
    """Mimics Jupiter Price v3: top-level {mint: {"usdPrice": <float>}}."""

    def __init__(self):
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        return httpx.Response(200, json={
            MINT_A: {"usdPrice": 150.5},
            MINT_B: {"usdPrice": 1.0},
        })


def _svc(handler):
    return PricingService(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), url="http://mock")


async def test_get_prices_parses():
    prices = await _svc(_CountingHandler()).get_prices([MINT_A, MINT_B])
    assert prices[MINT_A] == 150.5
    assert prices[MINT_B] == 1.0


async def test_unknown_mint_is_zero():
    handler = lambda req: httpx.Response(200, json={})  # mint absent from response
    prices = await _svc(handler).get_prices(["UNKNOWNMINT"])
    assert prices["UNKNOWNMINT"] == 0.0


async def test_cache_prevents_second_fetch():
    handler = _CountingHandler()
    svc = _svc(handler)
    await svc.get_prices([MINT_A])
    await svc.get_prices([MINT_A])  # served from cache
    assert handler.calls == 1


async def test_large_request_is_batched():
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        ids = req.url.params["ids"].split(",")
        return httpx.Response(200, json={m: {"usdPrice": 1.0} for m in ids})

    prices = await _svc(handler).get_prices([f"mint{i}" for i in range(120)])
    assert len(prices) == 120
    assert calls["n"] == 3  # ceil(120 / 50)
