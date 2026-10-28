# InvesThor Launch Guide

How to start the stack and check it works.

---

## Quick Launch (2 Commands)

```bash
# Step 1: Go to the project
cd trading_dashboard

# Step 2: Start the containers
docker-compose up -d
```

---

## Access

Once launched, visit:

| What | URL |
|------|-----|
| **Main Dashboard** | http://localhost:5174 |
| **API Documentation** | http://localhost:8001/docs |
| **Health Check** | http://localhost:8001/health |

---

## Containers

```
investhor_frontend   - Vue 3 dashboard (Terminal Ice UI)
investhor_backend    - FastAPI backend
investhor_db         - PostgreSQL
```

Check them with:
```bash
docker-compose ps
```

---

## Logs

```bash
# See all logs
docker-compose logs -f

# One container
docker-compose logs -f investhor_backend
docker-compose logs -f investhor_frontend
docker-compose logs -f investhor_db
```

---

## Smoke Test

### 1. Check if frontend loads
```bash
curl -I http://localhost:5174
# Look for: HTTP/1.1 200 OK
```

### 2. Check if API is alive
```bash
curl http://localhost:8001/health
# Look for: {"status": "healthy"}
```

### 3. Visit in Browser
Open: **http://localhost:5174**

You should see:
- The `INVESTHOR` ASCII logo and a `root@investhor:~#` prompt
- Tabs `[0] home  [1] dashboard  [2] trades  [3] profile`
- Near-black background, `#202d3d` panels, cyan accent, monospace text
- A cyan status bar at the bottom (orange in REAL mode)

---

## Useful Commands

```bash
# Stop everything
docker-compose stop

# Stop and remove (keeps data)
docker-compose down

# Stop and REMOVE EVERYTHING including data
docker-compose down -v

# Restart everything
docker-compose restart

# Rebuild images
docker-compose up -d --build

# Get shell access to backend
docker-compose exec investhor_backend sh

# Access database
docker-compose exec investhor_db psql -U trading_user -d trading_dashboard
```

---

## Troubleshooting

### Ports Already in Use?
```bash
# Find what's using port 5174
lsof -i :5174

# Find what's using port 8001
lsof -i :8001

# Kill it
kill -9 <PID>
```

### Containers Won't Start?
```bash
# Check what's wrong
docker-compose logs

# Try rebuilding
docker-compose down
docker-compose up -d --build
```

### Frontend Not Loading?
```bash
# Check frontend logs
docker-compose logs investhor_frontend

# Try refreshing: Ctrl+Shift+R (hard refresh)
```

### API Errors?
```bash
# Check backend logs
docker-compose logs investhor_backend

# Visit http://localhost:8001/docs to test endpoints
```

---

## Full Documentation

| Document | Purpose |
|----------|---------|
| **DOCKER_STARTUP.md** | Complete Docker guide |
| **CADDY_SETUP.md** | Deploy with Caddy proxy |
| **API_REFERENCE.md** | All API endpoints |
| **ARCHITECTURE.md** | System design |
| **README.md** | Full project docs |
| **CLAUDE.md** | Code structure and styling system |

---

## What's New

**Terminal Ice redesign** (replaces the old purple/gold Viking theme):
- Dark terminal look: near-black ground, `#202d3d` surfaces, cyan accent, orange for losses, no green
- JetBrains Mono everywhere, ASCII logo, `╔═[ title ]` panel headers, CLI-style labels
- New `tail -f sys.log` panel and a live ticker in the tab bar
- See INVESTHOR_CHANGES.md for the full list

**Container naming**:
- `investhor_frontend` (was trading_dashboard_ui)
- `investhor_backend` (was trading_dashboard_api)
- `investhor_db` (was trading_dashboard_db)

---

## Next Steps

1. **Run**: `docker-compose up -d`
2. **Visit**: http://localhost:5174
3. **Create account**: `POST /api/v1/paper-trading/accounts` (see below)
4. **Trade**: open `[1] dashboard` or `[2] trades` and fill `new_order.sh`
5. **Monitor**: watch `ps --positions` and `sys.log` on the dashboard
6. **Deploy**: follow CADDY_SETUP.md for production

---

## Key Endpoints

```bash
# Create Account
POST http://localhost:8001/api/v1/paper-trading/accounts
{
  "user_id": 1,
  "account_name": "My Account",
  "initial_balance": 10000
}

# Get Price
GET http://localhost:8001/api/v1/market/price/BTCUSDT

# Create Trade (what the web UI uses)
POST http://localhost:8001/api/v1/trades/
{
  "symbol": "BTCUSDT",
  "trade_type": "BUY",
  "entry_price": 43000,
  "stop_loss": 42000,
  "take_profit": 45000,
  "quantity": 0.5
}

# Create Trade (per account)
POST http://localhost:8001/api/v1/paper-trading/trades/1
{
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "trade_type": "BUY",
  "entry_price": 43000,
  "quantity": 0.5
}

# Close Trade
PUT http://localhost:8001/api/v1/paper-trading/trades/1
{
  "exit_price": 44000
}
```

---

## Learning Resources

- **Frontend**: Vue 3 docs + TradingView Lightweight Charts
- **Backend**: FastAPI docs at http://localhost:8001/docs
- **Database**: PostgreSQL + SQLAlchemy
- **DevOps**: Docker + Docker Compose

---

## System Requirements

- **CPU**: 2+ cores
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB free
- **Network**: For Binance API calls

---

## With Caddy Reverse Proxy

Want to expose to the internet? See **CADDY_SETUP.md**:

```
https://yourdomain.com/trading          → Frontend
https://yourdomain.com/trading/api/v1/* → API
```

---

## Support Checklist

If something doesn't work:

- [ ] Check: `docker-compose ps` (all showing "Up"?)
- [ ] Check logs: `docker-compose logs -f`
- [ ] Hard refresh browser: `Ctrl+Shift+R`
- [ ] Try: `docker-compose restart`
- [ ] Reset: `docker-compose down && docker-compose up -d --build`
- [ ] Check ports: `lsof -i :5174` and `lsof -i :8001`

---

*For detailed information, see DOCKER_STARTUP.md*
