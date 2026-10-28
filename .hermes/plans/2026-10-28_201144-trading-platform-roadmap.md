# InvesThor → Robust Personal Trading Platform — Build Plan

Date: 2026-10-28
Repo: `/home/preda/projects/trading_dashboard` (deployed at https://preda.home.ro/trading, behind Caddy basic-auth, 3 Docker containers on `homelab-bridge`)

---

## Goal

Turn InvesThor from a paper-trading demo into a robust single-user platform that: fixes paper trading, connects a Solana wallet and executes real swaps, exposes a bot API to place real/paper orders, tracks all assets, and runs backtests of strategies that are authored through an MCP server and visualized on the dashboard.

---

## Current context / assumptions

- Stack: FastAPI (`backend/app`), Vue 3 + Vite (`frontend`), PostgreSQL 16. DB schema is created **once** from `database/schema.sql` on first volume init — there is **no migration tool wired** (alembic is in `requirements.txt` but unused, no `alembic.ini`, no `tests/` dir).
- Two overlapping trade APIs exist:
  - `backend/app/api/trades.py` mounted at `/api/v1` → `POST/GET /api/v1/trades/`, `PATCH/DELETE /api/v1/trades/{id}`. **This is the path the frontend actually uses** (`frontend/src/pages/Trades.vue`).
  - `backend/app/api/paper_trading.py` mounted at `/api/v1/paper-trading` → account-scoped trades. Used only by `frontend/src/stores/trading.js`, which is **dead code** (Trades.vue uses raw `fetch`, not the store).
- **The paper-trade bug (root cause, confirmed from logs + DB):** `POST /api/v1/trades/` → `trades.py:create_trade` runs `account = db.query(PaperTradingAccount).first()`; on a fresh DB there are **0 users, 0 accounts, 0 trades**, so it raises `HTTPException(400, "No trading account found")`. There is no UI or startup path that creates a user/account. Also `GET /api/v1/paper-trading/accounts` returns **405** (no such route; only `POST /accounts` requiring `user_id`, and `GET /accounts/{id}`). So the account subsystem is half-wired.
- Secondary correctness bugs to fix alongside:
  - SELL/SHORT accounting: `paper_trading.py:create_trade` only debits balance for BUY and never models shorts; `trades.py` never touches balance at all. P&L sign for SELL is handled in `trades.py:close_trade` but not in `paper_trading.py:close_trade`.
  - `trade_type` is passed as a raw string into a `SQLEnum(TradeType)` column; works for `'BUY'/'SELL'` but is fragile.
- Market data: backend already fetches Binance **public** REST (`services/market_service.py`); browser streams Binance WS directly (`frontend/src/services/websocket.js`). No API keys required for data.
- Deploy/runtime facts: host ports bound to `127.0.0.1` only; public access is Caddy + basic-auth; `docker compose` is invoked with `sudo`; pytest is already installed in the backend image; `./backend` is bind-mounted into the container so new files appear live.
- Assumption: single operator (Preda). Multi-tenant auth is out of scope (YAGNI) beyond per-bot API keys.

---

## Architecture / proposed approach

Keep the FastAPI + Vue + Postgres core; add four backend subsystems behind clean service interfaces: (1) an **execution layer** with pluggable venues (`paper`, `solana`) sharing one order model, (2) a **wallet/asset layer** that reads Solana balances via RPC and prices via Jupiter, (3) a **backtesting engine** over historical Binance klines with a Python `Strategy` interface, and (4) a **Strategy MCP server** that authors strategy files and launches backtests. Introduce a lightweight SQL migration runner (not alembic) so the running DB can evolve, and add a pytest harness (SQLite in-memory + dependency override) so every change is TDD-driven. Real-money Solana trading defaults to **non-custodial browser signing (Phantom)** for manual trades, with an **opt-in, capped, encrypted hot-wallet** for bots.

---

## Decisions needed before building (gate Phases 4 and 6)

RESOLVED 2026-10-28:
1. Solana signing: **non-custodial** (browser/Phantom signs manual trades) **+ opt-in, capped, encrypted bot hot wallet** for unattended bots.
2. Real venues: **Solana (Jupiter) only** for real; everything else stays paper. No real Binance orders.
3. Strategy representation: **Python strategy classes** (`Strategy` base in `backend/strategies/`, authored by the MCP).
4. Live bots: **on-demand / cron-triggered** calls for now; no in-process scheduler yet (YAGNI).
5. Bot hot wallet guardrails: **$10/day USD cap**; **token allowlist** enforced in code — allowlist starts EMPTY (so the bot wallet can trade nothing until the operator populates it; empty = deny-all).
6. MCP server: **local/stdio, operator-only** (not publicly exposed); talks to backend over `127.0.0.1:8001` with a dedicated API key.

Original options (for reference):

These have recommended defaults baked into the plan; confirm or override before the gated phase starts.

1. **Solana signing model (gates Phase 4).** Recommended: non-custodial — the browser (Phantom/Solflare) builds+signs Jupiter swap transactions; the backend only prepares unsigned transactions and tracks results. Bots that must run unattended use a **separate, sparsely funded** hot wallet whose key is encrypted at rest (Fernet) and gated by per-day USD caps + token allowlist. Alternative: fully custodial server key (simpler bot UX, much higher risk). **Open: which, and what daily cap / token allowlist for the bot wallet?**
2. **Real CEX orders (gates Phase 2 "real" mode for Binance).** Recommended: Phase 2 ships `mode=paper` and `mode=solana` only; Binance real orders are deferred (needs funded Binance account + trade-enabled API keys + withdrawal risk). **Open: do you want real Binance orders at all, or Solana-only for real?**
3. **Strategy representation (gates Phase 5/6).** Recommended: strategies are Python files implementing a `Strategy` base class, stored in `backend/strategies/` and registered in a `strategies` table; the MCP writes these files. This is powerful for a programmer but executes arbitrary Python authored by you (acceptable single-user, self-hosted; still sandbox the backtest worker). Alternative: a constrained JSON rule DSL (safer, less expressive). **Open: Python strategies or JSON DSL?**
4. **Where the MCP runs (gates Phase 6).** Recommended: a stdio MCP server in `backend/mcp/` run locally by your agent, talking to the backend over `127.0.0.1:8001` with a dedicated API key. **Open: confirm the MCP is for your own agent only (not exposed publicly).**
5. **Scheduler for live bots (affects Phase 2/4).** Recommended: start with on-demand/cron-triggered bot calls; add an in-process APScheduler only when needed (YAGNI). **Open: do bots need sub-minute live loops now, or is cron-driven enough to start?**

---

## Conventions used by every task

- Run backend tests: `sudo docker compose -f ~/projects/trading_dashboard/docker-compose.yml exec -T backend pytest tests/ -q`
- Apply a new SQL migration to the live DB (Phase 0 builds the runner): `sudo docker compose exec -T backend python -m app.run_migrations`
- Commit after each green task: `git add -A && git commit -m "<msg>"` (run from `~/projects/trading_dashboard`).
- Every code task follows TDD: write failing test → run (red) → implement → run (green) → commit.
- New tables go in BOTH `database/schema.sql` (fresh installs) AND a numbered migration file (running DB). Keep them identical.

---

## Phase 0 — Test harness, migration runner, and the paper-trade fix

### Task 0.1 — Add pytest harness (SQLite in-memory + get_db override)
Files: create `backend/tests/__init__.py` (empty), `backend/tests/conftest.py`, `backend/pytest.ini`.

`backend/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

`backend/tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Verify (red baseline is fine — no tests yet):
```
sudo docker compose exec -T backend pytest tests/ -q
```
Expected: `no tests ran` (exit 5) — harness imports cleanly (no ImportError). Commit.

### Task 0.2 — Lightweight SQL migration runner
Files: create `backend/migrations/` dir, `backend/migrations/0001_init_marker.sql` (empty marker or `SELECT 1;`), `backend/app/run_migrations.py`.

`backend/app/run_migrations.py`:
```python
"""Apply ordered .sql files in backend/migrations exactly once. Tracked in schema_migrations."""
import os
from sqlalchemy import text
from app.database import engine

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")


def run() -> list[str]:
    applied: list[str] = []
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(filename VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())"
        ))
        done = {r[0] for r in conn.execute(text("SELECT filename FROM schema_migrations"))}
    for fn in sorted(os.listdir(MIGRATIONS_DIR)):
        if not fn.endswith(".sql") or fn in done:
            continue
        sql = open(os.path.join(MIGRATIONS_DIR, fn)).read()
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(text("INSERT INTO schema_migrations (filename) VALUES (:f)"), {"f": fn})
        applied.append(fn)
    return applied


if __name__ == "__main__":
    print("applied:", run())
```

Test `backend/tests/test_migrations.py`:
```python
def test_run_migrations_is_idempotent(monkeypatch, tmp_path):
    # Point the runner at a temp migrations dir with one file, run twice.
    import app.run_migrations as rm
    mig = tmp_path / "m"; mig.mkdir()
    (mig / "0001_x.sql").write_text("CREATE TABLE t_demo (id INTEGER);")
    monkeypatch.setattr(rm, "MIGRATIONS_DIR", str(mig))
    assert rm.run() == ["0001_x.sql"]
    assert rm.run() == []  # second run applies nothing
```
Note: this test needs the real Postgres engine; run it as an integration test inside the container (the `engine` is bound to `DATABASE_URL`). TDD cycle: write → red (`ModuleNotFoundError`/missing runner) → implement → green. Verify:
```
sudo docker compose exec -T backend pytest tests/test_migrations.py -q
```
Expected: `1 passed`. Commit.

### Task 0.3 — Startup bootstrap: default user + default paper account (fixes the bug)
Files: create `backend/app/services/account_service.py`; edit `backend/app/main.py`.

`backend/app/services/account_service.py`:
```python
import os
from sqlalchemy.orm import Session
from app.models import User, PaperTradingAccount

DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "preda")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "preda@localhost")
DEFAULT_ACCOUNT_NAME = os.getenv("DEFAULT_ACCOUNT_NAME", "main")
PAPER_STARTING_BALANCE = float(os.getenv("PAPER_STARTING_BALANCE", "100000"))


def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).filter(User.username == DEFAULT_USERNAME).first()
    if user:
        return user
    user = User(username=DEFAULT_USERNAME, email=DEFAULT_EMAIL)
    db.add(user); db.commit(); db.refresh(user)
    return user


def get_or_create_default_account(db: Session) -> PaperTradingAccount:
    acct = db.query(PaperTradingAccount).order_by(PaperTradingAccount.id).first()
    if acct:
        return acct
    user = get_or_create_default_user(db)
    acct = PaperTradingAccount(
        user_id=user.id,
        account_name=DEFAULT_ACCOUNT_NAME,
        initial_balance=PAPER_STARTING_BALANCE,
        current_balance=PAPER_STARTING_BALANCE,
        available_balance=PAPER_STARTING_BALANCE,
    )
    db.add(acct); db.commit(); db.refresh(acct)
    return acct
```

Edit `backend/app/main.py` — add after routers are included:
```python
from app.database import SessionLocal
from app.services.account_service import get_or_create_default_account

@app.on_event("startup")
def _bootstrap_default_account():
    db = SessionLocal()
    try:
        get_or_create_default_account(db)
    finally:
        db.close()
```

Test `backend/tests/test_account_bootstrap.py`:
```python
from app.services.account_service import get_or_create_default_account

def test_bootstrap_creates_user_and_account(db_session):
    acct = get_or_create_default_account(db_session)
    assert acct.id is not None
    assert acct.available_balance == acct.initial_balance
    # idempotent: second call returns same account
    assert get_or_create_default_account(db_session).id == acct.id
```
TDD: red (no module) → implement → green. Verify `pytest tests/test_account_bootstrap.py -q` → `2 passed` (one test, two asserts). Commit.

### Task 0.4 — Make `create_trade` self-heal (no more 400)
File: edit `backend/app/api/trades.py:create_trade`.
Replace:
```python
    account = db.query(PaperTradingAccount).first()
    if not account:
        raise HTTPException(status_code=400, detail="No trading account found")
```
with:
```python
    from app.services.account_service import get_or_create_default_account
    account = get_or_create_default_account(db)
```

Test `backend/tests/test_create_trade.py`:
```python
def test_post_trade_autocreates_account_and_succeeds(client):
    resp = client.post("/api/v1/trades/", json={
        "symbol": "BTCUSDT", "trade_type": "BUY",
        "entry_price": 50000, "quantity": 0.1,
        "stop_loss": 49000, "take_profit": 52000, "notes": "test",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["symbol"] == "BTCUSDT"
    assert body["is_open"] is True
```
TDD: with the old code this returns 400 (red); after the edit, 200 (green). Verify:
```
sudo docker compose exec -T backend pytest tests/test_create_trade.py -q
```
Expected: `1 passed`. Then confirm against the live DB end-to-end:
```
curl -s -u preda:<pw> -X POST https://preda.home.ro/trading/api/v1/trades/ \
  --resolve preda.home.ro:443:127.0.0.1 -H 'Content-Type: application/json' \
  -d '{"symbol":"BTCUSDT","trade_type":"BUY","entry_price":50000,"quantity":0.1}'
```
Expected: JSON with an `id`, HTTP 200. Commit.

### Task 0.5 — Restart backend to load the startup hook, verify bootstrap ran
Command:
```
sudo docker compose -f ~/projects/trading_dashboard/docker-compose.yml restart backend
sleep 4
sudo docker exec investhor_db psql -U trading_user -d trading_dashboard -tAc \
  "select (select count(*) from users), (select count(*) from paper_trading_accounts);"
```
Expected: `1|1`. Commit any doc updates.

---

## Phase 1 — Paper-trading correctness & consolidation

### Task 1.1 — Correct SHORT P&L + balance accounting in the live path
File: `backend/app/api/trades.py`. Define one helper and reuse it (DRY):
```python
def _realized_pl(trade_type, entry, exit_, qty):
    direction = 1 if str(trade_type).upper().endswith("BUY") else -1
    pl = direction * (exit_ - entry) * qty
    pct = (pl / (entry * qty) * 100) if entry and qty else 0.0
    return pl, pct
```
Use it in `DELETE /trades/{id}` (close) replacing the inline math. Add a `backend/tests/test_pl.py` covering BUY win, BUY loss, SELL win (exit < entry), SELL loss. TDD per case. Verify `pytest tests/test_pl.py -q` → `4 passed`. Commit.

### Task 1.2 — Debit/credit paper balance on open/close (BUY and SELL)
File: `backend/app/api/trades.py`. On open: reserve `entry_price*qty` from `available_balance` (reject if insufficient, like `paper_trading.py` does). On close: return proceeds and set `current_balance`. Add test `test_balance_roundtrip` asserting balance decreases on open and reflects P&L on close. TDD. Commit.

### Task 1.3 — Retire dead/duplicate code
Files: delete `frontend/src/stores/trading.js` (unused; Trades.vue uses raw fetch) OR rewire it to the live endpoints — **recommended: delete** (YAGNI). Grep to confirm no imports: `search_files pattern="stores/trading" `. Keep `paper_trading.py` only if Phase 2 reuses its account routes; otherwise mark its trade routes deprecated in a docstring. Commit.

### Task 1.4 — Add `GET /api/v1/paper-trading/accounts` (fix the 405)
File: `backend/app/api/paper_trading.py`. Add a list route returning all accounts (single-user → usually one). Test `test_list_accounts`. Commit.

---

## Phase 2 — Bot execution API (API keys + unified order execution)

Architecture: one execution entrypoint used by the UI, bots, and the MCP. An `ExecutionVenue` interface with `PaperVenue` (now) and `SolanaVenue` (Phase 4). API-key auth via FastAPI dependency.

### Task 2.1 — Schema: `api_keys` and extend `orders`
Files: `backend/migrations/0002_api_keys_and_orders.sql` + mirror in `database/schema.sql` + add SQLAlchemy models in `backend/app/models.py`.
```sql
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    label VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,          -- shown in UI, e.g. 'ith_live_ab12'
    key_hash VARCHAR(128) NOT NULL,           -- sha256 of full key
    scopes VARCHAR(255) NOT NULL DEFAULT 'paper:write',  -- CSV: paper:write, real:write, read
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS mode VARCHAR(10) NOT NULL DEFAULT 'paper';      -- paper|solana
ALTER TABLE orders ADD COLUMN IF NOT EXISTS api_key_id INTEGER REFERENCES api_keys(id);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS client_order_id VARCHAR(100);                   -- idempotency
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tx_signature VARCHAR(128);                       -- solana
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_client_id ON orders(api_key_id, client_order_id)
    WHERE client_order_id IS NOT NULL;
```
Apply: `sudo docker compose exec -T backend python -m app.run_migrations` → expect `applied: ['0002_api_keys_and_orders.sql']`. Commit.

### Task 2.2 — API-key generation + auth dependency
Files: `backend/app/services/apikey_service.py` (generate `secrets.token_urlsafe`, store sha256, return plaintext once), `backend/app/deps/auth.py` with `require_api_key(scope)` dependency that reads `Authorization: Bearer <key>` or `X-API-Key`, hashes, looks up active key, checks scope, updates `last_used_at`.
Tests `test_apikey.py`: generate → hash stored (not plaintext) → valid key passes `require_api_key('paper:write')` → wrong scope → 403 → unknown key → 401. TDD each. Commit.

### Task 2.3 — Execution venue interface + PaperVenue
Files: `backend/app/execution/base.py` (`class ExecutionVenue` with `place_order(order_req) -> OrderResult`), `backend/app/execution/paper.py` (reuses balance/trade logic from Phase 1), `backend/app/execution/__init__.py` with a `get_venue(mode)` factory.
Tests `test_paper_venue.py`: market BUY fills at provided/last price, creates a Trade + Order row, debits balance; idempotent on repeat `client_order_id`. TDD. Commit.

### Task 2.4 — Bot order endpoint
File: `backend/app/api/bot.py`, mounted at `/api/v1/bot`. `POST /orders` guarded by `require_api_key('paper:write')` (or `real:write` when `mode!='paper'`), body `{mode, symbol, side, type, quantity, price?, stop_loss?, take_profit?, client_order_id?}`. Returns the `OrderResult`. Add `GET /orders` (read scope) for bot reconciliation.
Tests `test_bot_api.py`: no key → 401; paper key + `mode=solana` → 403; valid paper order → 200 + persisted; duplicate `client_order_id` → same order (idempotent). TDD. Verify live:
```
# create a key via a one-off:
sudo docker compose exec -T backend python -c "from app.database import SessionLocal; from app.services.apikey_service import create_key; print(create_key(SessionLocal(),'bot-test','paper:write'))"
curl -s -u preda:<pw> --resolve preda.home.ro:443:127.0.0.1 \
  -H "X-API-Key: <printed_key>" -H 'Content-Type: application/json' \
  -d '{"mode":"paper","symbol":"SOLUSDT","side":"BUY","type":"MARKET","quantity":1,"price":150}' \
  https://preda.home.ro/trading/api/v1/bot/orders
```
Expected: 200 + order JSON. Commit. Document in `API_REFERENCE.md`.

### Task 2.5 — Rate limit + audit
Add simple per-key rate limiting (in-memory token bucket in `deps/auth.py`) and ensure every bot order writes an `orders` row with `api_key_id`. Test burst → 429. Commit.

---

## Phase 3 — Asset tracking (Solana read-only + unified portfolio)

### Task 3.1 — Schema: `wallets`
Files: `backend/migrations/0003_wallets.sql` + `database/schema.sql` + model.
```sql
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    chain VARCHAR(20) NOT NULL DEFAULT 'solana',
    address VARCHAR(64) NOT NULL,
    label VARCHAR(100),
    is_watch_only BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (chain, address)
);
```
Apply migration (expect `applied: ['0003_wallets.sql']`). Commit.

### Task 3.2 — Solana balance reader
File: `backend/app/services/solana_service.py`. Use JSON-RPC (`SOLANA_RPC_URL`) via `httpx`: `getBalance` (SOL) + `getTokenAccountsByOwner` (SPL tokens, parsed) → list of `{mint, amount, decimals}`. No private key needed. Add `.env` `SOLANA_RPC_URL` (default public mainnet; recommend a paid RPC later — see risks).
Tests `test_solana_service.py`: mock `httpx` responses, assert parsing of SOL + one SPL token. TDD. Commit.

### Task 3.3 — Token pricing via Jupiter
File: `backend/app/services/pricing_service.py`. `get_prices(mints: list[str]) -> {mint: usd}` via Jupiter Price API (`https://api.jup.ag/price/v2?ids=...`). Cache in-process (TTL 60s) to respect rate limits. Tests with mocked httpx. Commit.

### Task 3.4 — Unified portfolio endpoint
File: `backend/app/api/portfolio.py` at `/api/v1/portfolio`. `GET /summary` returns: paper account (cash + open positions valued at live Binance price) + each watched Solana wallet (token balances × Jupiter price) + a grand total, mirroring the structure of the existing `/home/preda/sysadmin/portfolio/portfolio.py` output so it is familiar. Reuse `market_service` for crypto marks.
Tests `test_portfolio_summary.py` with mocked solana + pricing + market services. TDD. Commit.

### Task 3.5 — Frontend: wallet management + portfolio view
Files: `frontend/src/pages/Profile.vue` (extend) + new `frontend/src/components/term/WalletPanel.vue`. Add a form to register a watch-only Solana address (`POST /api/v1/wallets`), list balances, and show the grand total. Verify in browser at `/trading` → [3] profile: balances render for a pasted address. Commit.

---

## Phase 4 — Real Solana trading (Jupiter) — GATED on Decision #1

Default design: **non-custodial**. Backend prepares an unsigned Jupiter swap; the browser signs with Phantom; backend records the resulting signature. Bots use an **opt-in encrypted hot wallet** with caps.

### Task 4.1 — Jupiter quote/swap service (prepare unsigned tx)
File: `backend/app/services/jupiter_service.py`. `get_quote(input_mint, output_mint, amount, slippage_bps)` via Jupiter `/swap/v1/quote`; `build_swap_tx(quote, user_pubkey)` via `/swap/v1/swap` returning a base64 unsigned versioned transaction. Tests with mocked httpx. Commit.

### Task 4.2 — Endpoints: quote + submit-signed
File: `backend/app/api/solana_trade.py` at `/api/v1/solana`. `POST /quote` (read), `POST /swap/prepare` → unsigned tx for a given wallet, `POST /swap/submit` → accept a client-signed, serialized tx, forward via RPC `sendTransaction`, poll confirmation, record an `orders` row with `mode='solana'` + `tx_signature`. Tests mock RPC. Commit.

### Task 4.3 — Frontend: Phantom connect + sign
Files: `frontend/src/services/phantom.js` (wallet-adapter or `window.solana`), `frontend/src/pages/Dashboard.vue` swap widget. Flow: connect → show quote → `prepare` → `window.solana.signAndSendTransaction` → `submit`. Manual verify with a tiny real swap on a low-value token (operator-confirmed). Commit.

### Task 4.4 — (Opt-in) Encrypted bot hot wallet — only if Decision #1 allows
Files: `backend/migrations/0004_bot_wallet.sql` (store Fernet-encrypted secret key + daily caps), `backend/app/services/hotwallet_service.py` (decrypt in-memory only, enforce `max_usd_per_day`, token allowlist), wire `SolanaVenue.place_order` to sign server-side. Secret: `WALLET_ENC_KEY` from a Docker secret, **never** in `.env` committed. Tests: cap exceeded → reject; disallowed token → reject. Commit. **Do not enable without explicit sign-off.**

---

## Phase 5 — Backtesting engine

### Task 5.1 — Historical data cache
Files: `backend/migrations/0005_ohlcv.sql` (`ohlcv(symbol, timeframe, ts, o,h,l,c,v)` with unique index), `backend/app/services/ohlcv_service.py` to fetch/backfill from Binance klines (reuse `market_service`) and upsert. Test upsert idempotency (mock httpx). Commit.

### Task 5.2 — Strategy interface + example
Files: `backend/strategies/__init__.py`, `backend/strategies/base.py`:
```python
from dataclasses import dataclass

@dataclass
class Signal:
    action: str   # "BUY" | "SELL" | "HOLD"
    size: float = 1.0

class Strategy:
    params: dict = {}
    def on_bar(self, i: int, bars) -> "Signal | None": ...
```
Plus `backend/strategies/sma_cross.py` (SMA fast/slow crossover) as the reference. Unit-test the signal logic on a synthetic series. Commit.

### Task 5.3 — Backtester core
File: `backend/app/backtest/engine.py`. Event loop over bars: apply signals, model fees/slippage (configurable bps), track equity curve, compute metrics (total return, max drawdown, Sharpe, win rate, #trades). Pure function, no DB. Tests `test_engine.py`: on a monotonically rising series an always-long strategy yields positive return equal to buy-and-hold minus fees. TDD. Commit.

### Task 5.4 — Schema + API to persist/run backtests
Files: `backend/migrations/0006_strategies_backtests.sql`:
```sql
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY, slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL, module VARCHAR(150) NOT NULL,  -- e.g. strategies.sma_cross
    params JSONB DEFAULT '{}', description TEXT, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY, strategy_id INTEGER REFERENCES strategies(id),
    symbol VARCHAR(50), timeframe VARCHAR(10), start_ts TIMESTAMPTZ, end_ts TIMESTAMPTZ,
    params JSONB DEFAULT '{}', status VARCHAR(20) DEFAULT 'pending',
    metrics JSONB, equity_curve JSONB, created_at TIMESTAMPTZ DEFAULT now());
```
File: `backend/app/api/backtest.py` at `/api/v1/backtest`: `POST /run` (loads strategy module by `module`, pulls OHLCV, runs engine synchronously for v1, stores metrics+curve), `GET /{id}`, `GET /` (list). Tests with the SMA strategy over cached/mocked OHLCV. TDD. Commit.
Note: v1 runs synchronously; if runs get slow, move to a background worker (APScheduler/RQ) — deferred (YAGNI).

### Task 5.5 — Frontend: backtest UI
Files: `frontend/src/pages/Backtest.vue` (+ route in `frontend/src/router/index.js`, + tab in `frontend/src/components/term/TermNav.vue`). Pick strategy + symbol + timeframe + date range → `POST /run` → render metrics and plot the equity curve on the existing chart component. Manual verify: run SMA on BTCUSDT 1h, see an equity curve + metrics. Commit.

---

## Phase 6 — Strategy MCP server — GATED on Decisions #3/#4

### Task 6.1 — MCP server scaffold
Files: `backend/mcp/server.py` (Python `mcp` stdio server), `backend/mcp/requirements.txt`. Config holds the backend base URL (`http://127.0.0.1:8001`) + a dedicated API key (scope `read` + a new `strategy:write`).

### Task 6.2 — MCP tools
Implement tools: `list_strategies`, `create_strategy(slug, name, python_source, params)` → writes `backend/strategies/<slug>.py` (validated: must subclass `Strategy`, no imports outside an allowlist) and inserts a `strategies` row; `run_backtest(slug, symbol, timeframe, start, end, params)` → calls `POST /api/v1/backtest/run`; `get_backtest(id)`. Each tool is a thin HTTP call to Phase-5 endpoints (DRY). 
Safety: strategy source is AST-validated (reject `import os`, `__import__`, `open`, `eval`, `exec`, network/file calls) before writing; backtests run in the backend worker only.

### Task 6.3 — Register MCP with the agent + smoke test
Add the server to the agent's MCP config (via `manage_connections` install/authorize). Smoke: ask the agent to "create an RSI-reversion strategy and backtest it on SOLUSDT 1h for the last 90 days" → verify a `strategies/` file appears, a `backtests` row is created, and the dashboard shows it. Commit.

---

## Cross-cutting tasks

- **Security:** keep all new write endpoints behind either the browser basic-auth (UI) or an API key (bots/MCP). Never log full API keys or wallet secrets. Add `WALLET_ENC_KEY` and any bot secrets via Docker secrets, not committed `.env`. Re-affirm memory rule: scripts/services must never call reboot/shutdown.
- **Config:** extend `backend/.env.example` with `SOLANA_RPC_URL`, `PAPER_STARTING_BALANCE`, `DEFAULT_USERNAME/EMAIL`, `WALLET_ENC_KEY` (commented). Mirror in root `.env` as needed; keep `.env` gitignored (already is).
- **CI-lite:** a `backend/run_tests.sh` wrapper running `pytest -q`; run it before each commit.
- **Docs:** update `API_REFERENCE.md` per new endpoint and `CLAUDE.md` "Quick Commands" with the test + migration commands.

---

## Tests / validation strategy

- Unit tests (SQLite in-memory via `conftest.py`) for all pure logic: P&L, backtester, pricing/solana parsing (httpx mocked), API-key hashing/scopes, idempotency.
- Integration tests (real Postgres, inside the backend container) for the migration runner and anything using JSONB/`ON CONFLICT`.
- Each task states its exact `pytest` invocation and expected `N passed`.
- Manual end-to-end checks (curl through Caddy with basic-auth; browser for UI) are specified where a human must confirm (real swaps, UI rendering).
- TDD loop per code task: red → implement → green → commit.

---

## Risks, tradeoffs, and open questions

- **Real-money Solana (highest risk).** Server-side signing = a hot wallet exposed to any backend RCE. Mitigations: non-custodial by default; if a bot key is used, cap daily USD, allowlist tokens, fund sparsely, encrypt at rest, isolate decryption. **Blocked on Decision #1.**
- **Arbitrary strategy code execution.** Python strategies are powerful but run author-supplied code. Single-user self-hosted lowers the risk; still AST-validate and never expose `create_strategy` publicly. If unacceptable, switch to the JSON DSL (Decision #3).
- **Public Solana RPC rate limits/reliability.** The default mainnet RPC throttles; plan to move to a paid RPC (Helius/Triton) before relying on balances/swaps in production.
- **Jupiter API shape/limits** can change; pin versions and handle non-200s; price cache mitigates rate limits.
- **Schema drift.** `schema.sql` (fresh) and `migrations/*.sql` (running) must be kept in sync by hand — every schema task edits both. Consider adopting alembic later if this becomes error-prone.
- **Backtest realism.** v1 ignores funding, partial fills, and liquidity; fees/slippage are flat bps. Good enough to compare strategies, not to promise live P&L.
- **Caddyfile edits on this host** use a read-only single-file bind mount — if Caddy routes change for new endpoints, apply via `docker cp` + `caddy reload --config /tmp/x` (none of the above phases require Caddy changes: all new routes live under the existing `/trading/api/*`).
- **Open questions:** Decisions #1–#5 above; also — desired default paper starting balance? which Solana tokens matter most for tracking/trading? do you want Binance real orders ever, or Solana-only for real?

---

## Suggested execution order & milestones

1. **M0 (fix + foundation):** Phase 0 + Phase 1 → paper trading works and is correct, tests + migrations exist. (Smallest, highest value; unblocks everything.)
2. **M1 (bots):** Phase 2 → API keys + paper order API; wire a first simple bot against paper.
3. **M2 (tracking):** Phase 3 → watch-only Solana + unified portfolio on the dashboard.
4. **M3 (backtests):** Phase 5 + Phase 6 → author strategies via MCP and backtest on the dashboard.
5. **M4 (real money, gated):** Phase 4 → non-custodial Phantom swaps, then optional capped bot wallet after sign-off.

Rationale: deliver the fix and a working paper+bot+tracking+backtest loop (no real-money risk) before touching live Solana execution.
