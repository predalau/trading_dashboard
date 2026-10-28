# InvesThor Strategy MCP Server

A local **stdio** MCP server that lets an MCP-capable agent author trading
strategies and run backtests on the InvesThor dashboard. It is a thin client
over the backend HTTP API and is intended for the operator's own agent only
(not publicly exposed).

## Tools

- `list_strategies()` — registered strategies.
- `create_strategy(slug, name, source, params, description)` — author a Python
  strategy. `source` must subclass `Strategy` from `strategies.base`; it is
  AST-validated server-side.
- `run_backtest(symbol, timeframe, strategy_slug|module, lookback, params)` —
  backtest over auto-backfilled OHLCV; returns metrics + a backtest id.
- `get_backtest(backtest_id)` — full result incl. equity curve.

## Setup

```bash
cd ~/projects/trading_dashboard/backend/mcp
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```

Mint a key with the right scopes (run in the backend container):

```bash
docker compose exec -T backend python -m scripts.create_api_key "mcp" "strategy:write,paper:write"
```

## Register with your agent

Add to your Hermes `config.yaml` under `mcp_servers` (adjust the venv python
path and key):

```yaml
mcp_servers:
  investhor-strategies:
    command: /home/preda/projects/trading_dashboard/backend/mcp/.venv/bin/python
    args: ["/home/preda/projects/trading_dashboard/backend/mcp/server.py"]
    env:
      TRADING_BACKEND_URL: http://127.0.0.1:8001
      TRADING_API_KEY: "ith_...your_key..."
```

The server talks to the backend on `127.0.0.1:8001`, bypassing the public
Caddy basic-auth layer, so no browser credentials are needed.
