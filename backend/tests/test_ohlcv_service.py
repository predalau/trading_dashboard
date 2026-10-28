import httpx

from app.services import ohlcv_service as svc


def _bars_handler(request: httpx.Request) -> httpx.Response:
    # Return 3 klines (< 1000 so pagination stops after one page).
    base = 1_700_000_000_000
    step = 3_600_000
    klines = [
        [base + i * step, "100", "110", "90", str(100 + i), "1000",
         base + (i + 1) * step - 1, "0", 0, "0", "0", "0"]
        for i in range(3)
    ]
    return httpx.Response(200, json=klines)


def _client():
    return httpx.AsyncClient(transport=httpx.MockTransport(_bars_handler))


async def test_fetch_and_backfill(db_session):
    n = await svc.backfill(db_session, "BTCUSDT", "1h", 1_700_000_000_000, 1_700_100_000_000, client=_client())
    assert n == 3
    rows = svc.get_ohlcv(db_session, "BTCUSDT", "1h")
    assert len(rows) == 3
    assert rows[0]["close"] == 100.0
    assert rows[2]["close"] == 102.0


async def test_backfill_is_idempotent(db_session):
    await svc.backfill(db_session, "BTCUSDT", "1h", 1_700_000_000_000, 1_700_100_000_000, client=_client())
    n2 = await svc.backfill(db_session, "BTCUSDT", "1h", 1_700_000_000_000, 1_700_100_000_000, client=_client())
    assert n2 == 0  # already cached
    assert len(svc.get_ohlcv(db_session, "BTCUSDT", "1h")) == 3
