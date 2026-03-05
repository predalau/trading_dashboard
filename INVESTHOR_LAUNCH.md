# ⚔️ InvesThor Launch Protocol

## The Viking Trading Warrior is Ready to Raid! 🛡️⚡

---

## 🚀 Quick Launch (2 Commands)

```bash
# Step 1: Enter the fortress
cd trading_dashboard

# Step 2: Awaken the warriors
docker-compose up -d
```

That's it! Your Viking trading empire is rising! 🏰

---

## 🌐 Access Your Empire

Once launched, visit:

| What | URL |
|------|-----|
| **Main Dashboard** | http://localhost:5174 |
| **API Documentation** | http://localhost:8001/docs |
| **Health Check** | http://localhost:8001/health |

---

## 🛡️ Your Containers (The Viking Crew)

```
⚔️  investhor_frontend   - Vue 3 Battle Dashboard
🛡️  investhor_backend    - FastAPI War Engine
💾  investhor_db         - PostgreSQL Vault
```

Check them with:
```bash
docker-compose ps
```

---

## 📊 Monitor Your Forces

```bash
# See all logs
docker-compose logs -f

# See specific warrior (choose one)
docker-compose logs -f investhor_backend
docker-compose logs -f investhor_frontend
docker-compose logs -f investhor_db
```

---

## 🎯 First Raid (Test Everything)

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
- ⚔️ InvesThor logo with Viking styling
- Gold/amber color scheme (Viking gold!)
- Navigation: Home, Dashboard, Raids
- Warrior aesthetic throughout

---

## 📝 Useful Commands

```bash
# Stop everything
docker-compose stop

# Stop and remove (keeps data)
docker-compose down

# Stop and REMOVE EVERYTHING including data ⚠️
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

## 🐛 Troubleshooting

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

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| **DOCKER_STARTUP.md** | Complete Docker guide |
| **CADDY_SETUP.md** | Deploy with Caddy proxy |
| **API_REFERENCE.md** | All API endpoints |
| **ARCHITECTURE.md** | System design |
| **README.md** | Full project docs |

---

## 🏆 What's New with InvesThor

✨ **Viking Branding**:
- ⚔️ Sword and shield icons
- 🛡️ Gold/amber color scheme (Norse warrior gold!)
- 🌩️ Thunder symbols (⚡)
- 📜 Battle-themed naming:
  - "Raids" instead of "Trades"
  - "Battle Command Center" instead of "Dashboard"
  - "Plan Your Raid" for trade forms
  - "Chronicles of Battle" for trade history

🎨 **Visual Updates**:
- Viking-inspired gold borders and accents
- Enhanced glass-morphism with amber tones
- Gradient buttons with shadow effects
- Footer saying "Valhalla awaits the bold traders ⚡"

🏗️ **Container Naming**:
- `investhor_frontend` (was trading_dashboard_ui)
- `investhor_backend` (was trading_dashboard_api)
- `investhor_db` (was trading_dashboard_db)

---

## ⚡ Next Steps

1. ✅ **Run**: `docker-compose up -d`
2. ✅ **Visit**: http://localhost:5174
3. ✅ **Create Account**: Click "Begin Your Saga" on home page
4. ✅ **Launch Raid**: Go to "Raids" tab and create a trade
5. ✅ **Monitor**: Check "Dashboard" for battle command center
6. ✅ **Deploy**: Follow CADDY_SETUP.md for production

---

## 🎯 Key Endpoints

```bash
# Create Account
POST http://localhost:8001/api/v1/paper-trading/accounts
{
  "user_id": 1,
  "account_name": "My Saga",
  "initial_balance": 10000
}

# Get Price
GET http://localhost:8001/api/v1/market/price/BTCUSDT

# Create Trade (Raid)
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

## 🎓 Learning Resources

- **Frontend**: Vue 3 docs + TradingView Lightweight Charts
- **Backend**: FastAPI docs at http://localhost:8001/docs
- **Database**: PostgreSQL + SQLAlchemy
- **DevOps**: Docker + Docker Compose

---

## 🤖 System Requirements

- **CPU**: 2+ cores
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB free
- **Network**: For Binance API calls

---

## 🌐 With Caddy Reverse Proxy

Want to expose to the internet? See **CADDY_SETUP.md**:

```
https://yourdomain.com/trading          → Frontend
https://yourdomain.com/trading/api/v1/* → API
```

---

## 📞 Support Checklist

If something doesn't work:

- [ ] Check: `docker-compose ps` (all showing "Up"?)
- [ ] Check logs: `docker-compose logs -f`
- [ ] Hard refresh browser: `Ctrl+Shift+R`
- [ ] Try: `docker-compose restart`
- [ ] Reset: `docker-compose down && docker-compose up -d --build`
- [ ] Check ports: `lsof -i :5174` and `lsof -i :8001`

---

## 🎉 You're Ready!

```
Your Viking Empire Awaits! ⚔️

╔═══════════════════════════════════════╗
║   ⚔️ InvesThor Trading Warrior ⚡    ║
║                                       ║
║   Status: READY FOR BATTLE            ║
║   Containers: investhor_*             ║
║   Frontend: localhost:5174            ║
║   Backend: localhost:8001             ║
║                                       ║
║   May your trades be glorious! 🛡️   ║
╚═══════════════════════════════════════╝
```

**Valhalla awaits the bold traders!** ⚡

---

*For detailed information, see DOCKER_STARTUP.md*
