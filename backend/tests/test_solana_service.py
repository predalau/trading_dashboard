import json

import httpx

from app.services.solana_service import SolanaService, SOL_MINT


def _handler(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    method = body["method"]
    if method == "getBalance":
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"value": 2_500_000_000}})
    if method == "getTokenAccountsByOwner":
        return httpx.Response(200, json={
            "jsonrpc": "2.0", "id": 1,
            "result": {"value": [
                {"account": {"data": {"parsed": {"info": {
                    "mint": SOL_MINT,
                    "tokenAmount": {"uiAmount": 12.5, "decimals": 6},
                }}}}},
                {"account": {"data": {"parsed": {"info": {
                    "mint": "ZEROMINT",
                    "tokenAmount": {"uiAmount": 0, "decimals": 6},  # filtered out
                }}}}},
            ]},
        })
    return httpx.Response(500, json={"error": "unexpected"})


def _svc():
    client = httpx.AsyncClient(transport=httpx.MockTransport(_handler))
    return SolanaService(rpc_url="http://mock", client=client)


async def test_get_sol_balance():
    sol = await _svc().get_sol_balance("addr")
    assert sol == 2.5  # 2.5e9 lamports


async def test_get_token_balances_filters_zero():
    tokens = await _svc().get_token_balances("addr")
    assert len(tokens) == 1
    assert tokens[0]["mint"] == SOL_MINT
    assert tokens[0]["amount"] == 12.5


async def test_get_wallet_balances_combined():
    bal = await _svc().get_wallet_balances("addr")
    assert bal["sol"] == 2.5
    assert len(bal["tokens"]) == 1
