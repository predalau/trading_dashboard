# 🛡️ START HERE - InvesThor Quick Start

## The Legendary 2-Command Launch! ⚔️⚡

Welcome to **InvesThor** - The Viking Trading Warrior! 

This is your fastest path to glory. Just 2 commands and you're trading!

---

## 🚀 Launch Your Empire (2 Commands)

### Command 1: Go to Project
```bash
cd /home/preda/trading_dashboard
```

### Command 2: Awaken the Warriors
```bash
docker-compose up -d
```

**That's it!** Your fleet is rising! 🏰

---

## 🌐 Access Your Dashboard

### **Main Trading Dashboard**
👉 **http://localhost:5174** ⚔️

This is where the magic happens! You'll see:
- ⚔️ InvesThor logo (Viking warrior)
- 🛡️ Golden Viking-themed interface
- Navigation: Home, Dashboard, Raids
- Gold and amber colors (Viking gold!)

### **API Documentation**
👉 **http://localhost:8001/docs**

Test all API endpoints interactively here!

---

## ✅ Verify Everything Works

### Step 1: Check Containers Are Running
```bash
docker-compose ps
```

You should see:
```
investhor_frontend   Up 2 minutes
investhor_backend    Up 2 minutes
investhor_db         Up 2 minutes
```

### Step 2: Test the API
```bash
curl http://localhost:8001/health
```

Should return: `{"status": "healthy"}`

### Step 3: Open Browser
Open: **http://localhost:5174**

See the InvesThor logo? ⚔️ You're ready!

---

## 🎯 Your First Trade (Raid!)

1. **Open** http://localhost:5174
2. **Click** "Begin Your Saga" (Home page)
3. **Create** a paper trading account with $10,000
4. **Click** "Raids" in navigation
5. **Plan** your first raid:
   - Symbol: BTCUSDT
   - Type: BUY
   - Entry Price: 43000
   - Quantity: 0.5
6. **Click** "⚔️ Launch Raid"
7. **Monitor** on Dashboard

Congratulations! You've conquered your first trade! 🏆

---

## 📊 What You Can Do

### 📈 Dashboard (Battle Command Center)
- View your War Chest (account balance)
- Track Empire Worth (portfolio value)
- Monitor Active Raids (open positions)
- See Glory Rate (win percentage)
- View Bitcoin battle chart

### 🛡️ Raids (Trading Hall)
- Plan new raids (create trades)
- View active conquests (open positions)
- End your raids (close positions)
- Read Chronicles of Battle (trade history)

### 🌐 API
- Create accounts programmatically
- Execute trades via REST API
- Get real-time market prices
- Integrate with your own systems

---

## 🛠️ Useful Commands

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

## 🐛 Something Not Working?

### Frontend won't load?
```bash
# Hard refresh browser: Ctrl+Shift+R
# Check logs:
docker-compose logs investhor_frontend
```

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

### Still stuck?
See **DOCKER_STARTUP.md** for complete troubleshooting!

---

## 📚 Documentation Index

| Want to... | Read This |
|-----------|-----------|
| **Quick 5-min setup** | ← You are here! |
| **Full Docker guide** | DOCKER_STARTUP.md |
| **Deploy with Caddy** | CADDY_SETUP.md |
| **All API endpoints** | API_REFERENCE.md |
| **What changed** | INVESTHOR_CHANGES.md |
| **System architecture** | ARCHITECTURE.md |

---

## 🎨 What's New with InvesThor?

Your trading dashboard now has **VIKING VIBES!** ⚔️

✨ **Golden warrior theme**
- Gold/amber colors throughout
- ⚔️ Sword and shield icons
- 🛡️ Battle-themed naming
- ⚡ Thunder and lightning effects

🏰 **Warrior-inspired interface**
- "Raids" instead of "Trades"
- "Battle Command Center" dashboard
- "Plan Your Raid" forms
- "Chronicles of Battle" history
- "Valhalla awaits the bold traders" footer

🎯 **Container names**
- `investhor_frontend` (your battlefield)
- `investhor_backend` (your war engine)
- `investhor_db` (your treasure vault)

---

## ⚡ Next Level Features

### Paper Trading
Trade with virtual money - no risk, only glory!

### Real Market Data
Connected to Binance API for real prices

### Interactive Charts
TradingView professional charts showing your battles

### REST API
Build bots and automate your raiding strategies

### Live Analytics
Track win rates, profits, and trading statistics

---

## 🏆 Common Tasks

### View Running Containers
```bash
docker ps | grep investhor
```

### Access Database Directly
```bash
docker-compose exec investhor_db psql -U trading_user -d trading_dashboard
# Then: SELECT * FROM trades;
```

### Get Backend Shell
```bash
docker-compose exec investhor_backend sh
```

### Backup Your Trades
```bash
docker-compose exec investhor_db pg_dump -U trading_user trading_dashboard > backup.sql
```

---

## 🚀 Ready to Deploy?

Want to share with the world? See **CADDY_SETUP.md** to:
- Deploy on your server
- Use a custom domain
- Enable HTTPS
- Protect with authentication

Access via: `https://yourdomain.com/trading`

---

## 💪 You've Got This!

```
╔════════════════════════════════════════╗
║  🛡️ InvesThor Trading Warrior 🛡️    ║
║                                        ║
║     Ready to Conquer Markets?          ║
║                                        ║
║  1. docker-compose up -d               ║
║  2. Open http://localhost:5174         ║
║  3. Begin Your Saga!                   ║
║                                        ║
║     Valhalla Awaits! ⚔️⚡           ║
╚════════════════════════════════════════╝
```

---

## 🎯 Quick Links

- **Dashboard**: http://localhost:5174
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## 📞 Help

Stuck? Don't worry!
1. Check: `docker-compose logs -f`
2. Try: `docker-compose restart`
3. Read: DOCKER_STARTUP.md
4. Ask: Check INVESTHOR_CHANGES.md for what's new

---

**May your trades be glorious and your portfolio ever-growing!** 🏆⚔️

*InvesThor - The Viking Way to Trade* ⚡
