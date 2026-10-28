# InvesThor Changes

## Latest: Terminal Ice redesign (2026-10-28, PR #1)

The purple/gold Viking theme is gone. The frontend now uses **Terminal Ice**, a dark terminal-style interface. Logic, API calls and routes are unchanged, except for the new `sys.log` panel.

### Look

| Token | Value | Used for |
| --- | --- | --- |
| `--bg` | `#0c0f14` | Page ground |
| `--panel` | `#151a22` | Chart and log panels |
| `--surface` | `#202d3d` | Tab bar, order form, positions table |
| `--line` | `#2c3d52` | Borders, dividers |
| `--grid` | `#1c2838` | Chart grid |
| `--text` | `#d6e2f0` | Body text |
| `--muted` | `#8a9bb0` | Labels, timestamps |
| `--accent` / `--up` | `#4fd6ff` | Active tab, primary buttons, gains, up candles |
| `--down` | `#ff8a5c` | Losses, SL, short, hollow down candles, REAL mode |
| `--tp` | `#c7b8ff` | Take-profit |
| `--on-accent` | `#0a0f15` | Text on cyan / orange buttons |

- JetBrains Mono everywhere (self-hosted), 13px base, tabular numbers
- Square corners, no gradients, no emoji, no green
- Faint CRT scanlines and a blinking block caret, both off under `prefers-reduced-motion`
- Tokens live on `:root` in `frontend/src/style.css`; Tailwind `term-*` colours point at them; the chart reads them too

### App shell
- **Header**: `INVESTHOR` ASCII logo, a `root@investhor:~/<page>#` prompt with a command per page, `PAPER` / `REAL` buttons. REAL adds an orange top border.
- **Tab bar**: `[0] home  [1] dashboard  [2] trades  [3] profile`, number keys switch tabs, live BTC/ETH/SOL ticker and a `ws ●` connection dot.
- **Status bar**: `[investhor] 1:dashboard*`, mode, equity, UTC clock. Turns orange in REAL mode.
- **Mobile** (under 768px): compact `investhor:~$` logo, square bottom tabs, no ticker.

### Pages
- **Home**: `boot.log`, `cat motd`, `help` command list, `ls integrations/`
- **Dashboard**:
  - Chart header `╔═[ BTC/USDT ▾ ]═` with live 24h price and change, timeframes `1h 4h 1d 1w`
  - `new_order.sh`: LONG/SHORT, `--entry --sl --tp --qty`, live risk / reward / r:r and an ASCII r:r bar, `$ ./execute --paper`
  - `tail -f sys.log`: WebSocket events, fills, SL/TP hits, chart picks, API errors
  - `ps --positions`: hex PID, live mark and P&L, R, total unrealized, `kill -9` with confirm
- **Trades**: `new_order.sh` with notes, `ps --positions`, `close_position.sh` dialog, `cat history.log` (newest first)
- **Profile**: equity, total P&L, win rate, average realized R tiles, `whoami` panel, history

### Files
- New: `frontend/src/components/term/` (TermPanel, TermHeader, TermNav, TickerStrip, StatusBar, SysLog, HistoryTable, AsciiLogo), `frontend/src/stores/log.js`, `frontend/public/favicon.svg`
- Rewritten: `App.vue`, all pages, `style.css`, `tailwind.config.js`
- Touched: `ChartComponent.vue` (theme), `services/websocket.js` and `api/client.js` (log events), `index.html` (title, favicon), `main.js` (font)
- Removed: old `dark` / `secondary` / `accent` Tailwind colours, glass / card / gradient button styles, fade and slide animations

### Upgrading an existing install
The redesign adds an npm dependency (`@fontsource/jetbrains-mono`). The frontend container keeps `node_modules` in an anonymous volume, so rebuild and renew it:
```bash
docker-compose up -d --build -V frontend
```

### Known gaps
- The trades API does not return `profit_loss` or `exit_time`. History and Profile derive P&L from `exit_price`.
- The frontend asks for `GET /paper-trading/accounts` (a list), but the backend only has `GET /paper-trading/accounts/{id}`. Status bar equity and Profile balances fall back to defaults until that endpoint exists.
- `npm run lint` needs an ESLint config; the repo has none.

### Rollback
```bash
git revert -m 1 a389ddc   # the PR #1 merge commit
```

---

## Earlier: container rename

```
OLD                          NEW
trading_dashboard_api    →   investhor_backend
trading_dashboard_ui     →   investhor_frontend
trading_dashboard_db     →   investhor_db
```

Environment variables did not change. See DOCKER_STARTUP.md.

The Viking UI theme from that release (gold/purple, battle naming, emoji) has been fully replaced by Terminal Ice above.
