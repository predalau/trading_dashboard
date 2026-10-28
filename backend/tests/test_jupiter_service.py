import httpx
import pytest

from app.services.jupiter_service import JupiterService, JupiterError

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/quote"):
        return httpx.Response(200, json={
            "inputMint": SOL, "outputMint": USDC,
            "inAmount": "10000000", "outAmount": "1024606", "slippageBps": 50,
        })
    if request.url.path.endswith("/swap"):
        return httpx.Response(200, json={
            "swapTransaction": "AQAAAABASE64==", "lastValidBlockHeight": 440652834,
            "simulationError": None,
        })
    return httpx.Response(404)


def _svc(handler=_handler):
    return JupiterService(base_url="http://mock/swap/v1",
                          client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


async def test_get_quote():
    q = await _svc().get_quote(SOL, USDC, 10_000_000, 50)
    assert q["outAmount"] == "1024606"


async def test_zero_amount_rejected():
    with pytest.raises(JupiterError):
        await _svc().get_quote(SOL, USDC, 0)


async def test_build_swap_tx_returns_unsigned():
    out = await _svc().build_swap_tx({"any": "quote"}, "SomePubkey")
    assert out["swap_transaction"] == "AQAAAABASE64=="
    assert out["last_valid_block_height"] == 440652834


async def test_simulation_error_raises():
    def h(req):
        return httpx.Response(200, json={"swapTransaction": "x", "simulationError": "boom"})
    with pytest.raises(JupiterError):
        await _svc(h).build_swap_tx({"q": 1}, "pk")
