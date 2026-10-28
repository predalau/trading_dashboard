"""InvesThor strategy MCP server (stdio).

Exposes strategy authoring + backtesting to an MCP-capable agent. It is a thin
client over the InvesThor backend HTTP API; it holds an API key with the
'strategy:write' scope and talks to the backend on 127.0.0.1 (bypassing the
public Caddy basic-auth layer).

Env:
  TRADING_BACKEND_URL  default http://127.0.0.1:8001
  TRADING_API_KEY      an API key with scope 'strategy:write' (+ 'paper:write')
"""
import os

import httpx
from mcp.server.fastmcp import FastMCP

BACKEND = os.getenv("TRADING_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
API_KEY = os.getenv("TRADING_API_KEY", "")

mcp = FastMCP("investhor-strategies")


def _headers() -> dict:
    return {"X-API-Key": API_KEY} if API_KEY else {}


def _unwrap(resp: httpx.Response):
    if resp.status_code >= 400:
        try:
            return {"error": resp.json().get("detail", resp.text)}
        except Exception:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    return resp.json()


@mcp.tool()
def list_strategies() -> list:
    """List registered trading strategies (slug, module, params)."""
    return _unwrap(httpx.get(f"{BACKEND}/api/v1/backtest/strategies", timeout=20))


@mcp.tool()
def create_strategy(slug: str, name: str, source: str,
                    params: dict | None = None, description: str = "") -> dict:
    """Create/update a Python strategy.

    `source` MUST define a class subclassing Strategy imported from
    strategies.base and implement on_bar(self, i, bars) -> Signal | None.
    Source is AST-validated server-side (no imports except strategies.base, no
    dangerous builtins). Returns the created strategy or an {"error": ...}.
    """
    body = {"slug": slug, "name": name, "source": source,
            "params": params or {}, "description": description}
    return _unwrap(httpx.post(f"{BACKEND}/api/v1/backtest/strategies",
                              headers=_headers(), json=body, timeout=30))


@mcp.tool()
def run_backtest(symbol: str, timeframe: str = "1h", strategy_slug: str = "",
                 module: str = "", lookback: int = 500,
                 params: dict | None = None) -> dict:
    """Run a backtest over cached (auto-backfilled) OHLCV.

    Provide either strategy_slug (a registered strategy) or module
    (e.g. 'strategies.sma_cross'). Returns metrics (total_return,
    buy_hold_return, max_drawdown, sharpe, win_rate, num_trades) + a backtest id.
    """
    body = {"symbol": symbol, "timeframe": timeframe, "lookback": lookback,
            "params": params or {}}
    if strategy_slug:
        body["strategy_slug"] = strategy_slug
    if module:
        body["module"] = module
    return _unwrap(httpx.post(f"{BACKEND}/api/v1/backtest/run", json=body, timeout=120))


@mcp.tool()
def get_backtest(backtest_id: int) -> dict:
    """Fetch a backtest result including its equity curve."""
    return _unwrap(httpx.get(f"{BACKEND}/api/v1/backtest/{backtest_id}", timeout=20))


if __name__ == "__main__":
    mcp.run()
