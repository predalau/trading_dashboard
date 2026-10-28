# START HERE: InvesThor Quick Start

Two commands and you're trading.

---

## Launch (2 commands)

### 1. Go to the project
```bash
cd /home/preda/trading_dashboard
```

### 2. Start the containers
```bash
docker-compose up -d
```

---

## Open the app

### Trading dashboard
**http://localhost:5174**

You should see the Terminal Ice interface:
- The `INVESTHOR` ASCII logo and a `root@investhor:~#` prompt line
- tmux-style tabs: `[0] home`, `[1] dashboard`, `[2] trades`, `[3] profile` (press `0` to `3` to switch)
- A live BTC / ETH / SOL ticker and a cyan status bar at the bottom
- Dark near-black background, `#202d3d` panels, cyan accent, JetBrains Mono

### API documentation
**http://localhost:8001/docs**

---

## Verify everything works

### 1. Containers are running
```bash
docker-compose ps
```

You should see:
```
investhor_frontend   Up 2 minutes
investhor_backend    Up 2 minutes
investhor_db         Up 2 minutes
```

### 2. The API answers
```bash
curl http://localhost:8001/health
```

Should return: `{"status": "healthy"}`

### 3. The browser loads
Open **http://localhost:5174**. If the ASCII logo shows and the `ws` dot in the tab bar turns cyan, the live feed is connected.

---

## Your first trade

1. Make sure a paper trading account exists (create one via `POST /api/v1/paper-trading/accounts` in the API docs).
2. Open **[1] dashboard**.
3. Pick a pair in the chart header (`BTC/USDT ▾`).
4. In `new_order.sh`:
   - Choose `LONG` or `SHORT`
   - Fill `--entry`, `--sl`, `--tp`, `--qty` (or press `+` and click the chart to set a price)
   - Check the risk / reward line
5. Press `$ ./execute --paper`.
6. Watch the position in `ps --positions` and the fill in `tail -f sys.log`.

---

## What you can do

### [1] dashboard
- Live candlestick chart with entry, SL and TP lines
- Live price and 24h change for the selected pair
- `new_order.sh` order form with risk / reward and r:r bar
- `tail -f sys.log`: connections, fills, SL/TP hits, errors
- `ps --positions`: open trades with live P&L and R; `kill -9` closes one (with confirm)
- Trades auto-close when the live price hits SL or TP

### [2] trades
- Place trades for any listed pair, with notes
- See and close open positions (`close_position.sh` asks for the exit price)
- `cat history.log`: closed trades, newest first

### [3] profile
- Equity, total P&L, win rate, average realized R
- `whoami` account details and the trade history

### API
- Create accounts and trades programmatically
- Get market prices and candles
- See **API_REFERENCE.md**

---

## Useful commands

```bash
# Stop everything
docker-compose stop

# View logs (troubleshooting)
docker-compose logs -f

# View backend logs only
docker-compose logs -f investhor_backend

# View frontend logs only
docker-compose logs -f investhor_frontend

# Restart everything
docker-compose restart

# Rebuild (if you made code changes)
docker-compose up -d --build

# Stop and remove everything
docker-compose down

# Complete reset (removes data!)
docker-compose down -v
```

---

## Something not working?

### Frontend won't load?
```bash
# Hard refresh browser: Ctrl+Shift+R
# Check logs:
docker-compose logs investhor_frontend
```

### Chart stuck on `[..] loading`, or the `ws` dot is orange?
The browser can't reach `stream.binance.com:9443`, or the backend `/market/klines` call failed. `sys.log` shows `[ERR]` lines with the reason.

### API not responding?
```bash
# Check backend is running:
curl http://localhost:8001/health

# Check logs:
docker-compose logs investhor_backend
```

### Port already in use?
```bash
# Find what's using port 5174:
lsof -i :5174

# Find what's using port 8001:
lsof -i :8001

# Kill the process:
kill -9 <PID>
```

### Blank page or "Failed to resolve @fontsource/jetbrains-mono" after updating?
The frontend's `node_modules` lives in an anonymous volume. Rebuild and renew it:
```bash
docker-compose up -d --build -V frontend
```

### Still stuck?
See **DOCKER_STARTUP.md** for full troubleshooting.

---

## Documentation index

| Want to... | Read this |
|-----------|-----------|
| **Quick 5-min setup** | You are here |
| **Full Docker guide** | DOCKER_STARTUP.md |
| **Deploy with Caddy** | CADDY_SETUP.md |
| **All API endpoints** | API_REFERENCE.md |
| **What changed** | INVESTHOR_CHANGES.md |
| **System architecture** | ARCHITECTURE.md |
| **Working on the code** | CLAUDE.md |

---

## Common tasks

### View running containers
```bash
docker ps | grep investhor
```

### Access the database directly
```bash
docker-compose exec investhor_db psql -U trading_user -d trading_dashboard
# Then: SELECT * FROM trades;
```

### Get a backend shell
```bash
docker-compose exec investhor_backend sh
```

### Back up your trades
```bash
docker-compose exec investhor_db pg_dump -U trading_user trading_dashboard > backup.sql
```

---

## Ready to deploy?

See **CADDY_SETUP.md** to:
- Deploy on your server
- Use a custom domain
- Enable HTTPS
- Protect with authentication

Access via: `https://yourdomain.com/trading`

---

## Quick links

- **Dashboard**: http://localhost:5174
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
