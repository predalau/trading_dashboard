# Bot / MCP API

API-key-authenticated endpoints for programmatic order execution. Mounted at
`/api/v1/bot` (publicly reachable as `https://preda.home.ro/trading/api/v1/bot/*`,
which also sits behind the dashboard's HTTP basic-auth).

## Authentication

Every request needs an API key, sent either way:

- `X-API-Key: ith_...`
- `Authorization: Bearer ith_...`

Keys carry CSV **scopes**:

- `paper:write` — place paper orders (`mode=paper`)
- `real:write`  — place real orders (`mode=solana`; venue lands in Phase 4)
- `read`        — reserved for read-only use

### Mint a key

Inside the backend container (prints the plaintext once; only its hash is stored):

```bash
docker compose exec -T backend python -m scripts.create_api_key "my-bot" paper:write
```

## POST /api/v1/bot/orders

Place an order. Rate-limited per key (default 10 req/s → HTTP 429).

Request body:

```json
{
  "mode": "paper",
  "symbol": "SOLUSDT",
  "side": "BUY",
  "type": "MARKET",
  "quantity": 1.0,
  "price": 150.0,
  "stop_loss": null,
  "take_profit": null,
  "client_order_id": "my-unique-id",
  "notes": null
}
```

- `mode`: `paper` (now) or `solana` (Phase 4). Non-paper requires `real:write`.
- `price`: optional for `MARKET` — fills at the last Binance price if omitted.
- `client_order_id`: optional idempotency key. Re-posting the same
  `(api_key, client_order_id)` returns the original order with
  `"idempotent_replay": true` and creates nothing new.

Responses:

- `200` → `OrderResult` JSON (`order_id`, `status`, `filled_price`, `trade_id`, ...)
- `400` → bad input, unsupported mode, or insufficient paper balance
- `401` → missing/invalid key
- `403` → key lacks the scope for this mode
- `429` → per-key rate limit exceeded

## GET /api/v1/bot/orders?limit=50

List orders placed by the calling key (newest first) for reconciliation.
