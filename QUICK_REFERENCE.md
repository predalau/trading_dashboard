# Quick Reference Guide

## Essential Commands

### Start Development Servers

```bash
# Start all services with Docker
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Backend Commands

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
python -m uvicorn app.main:app --reload

# Run on specific port
python -m uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/

# Run specific test file
pytest tests/test_trading.py

# Access API documentation
http://localhost:8000/docs
```

### Frontend Commands

```bash
# Install dependencies
npm install

# Start development server (hot-reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Format code
npm run lint -- --fix
```

### Database Commands

```bash
# Connect to database
psql -U trading_user -d trading_dashboard

# List tables
\dt

# View specific table
SELECT * FROM trades;

# Reset database (CAUTION: deletes data)
dropdb -U trading_user trading_dashboard
createdb -U trading_user trading_dashboard
psql -U trading_user -d trading_dashboard -f database/schema.sql

# Export data
pg_dump -U trading_user trading_dashboard > backup.sql

# Import data
psql -U trading_user trading_dashboard < backup.sql
```

---

## URLs & Ports

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Trading Dashboard UI |
| Backend | http://localhost:8000 | API Server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API Docs |
| PostgreSQL | localhost:5432 | Database |

---

## Typical Workflow

### 1. Create Paper Trading Account
```bash
curl -X POST http://localhost:8000/api/v1/paper-trading/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "account_name": "My Account",
    "initial_balance": 10000
  }'
```

### 2. Check Bitcoin Price
```bash
curl http://localhost:8000/api/v1/market/price/BTCUSDT
```

### 3. Place a BUY Trade
```bash
curl -X POST http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "exchange": "BINANCE",
    "trade_type": "BUY",
    "entry_price": 43000,
    "quantity": 0.5
  }'
```

### 4. Close the Trade
```bash
curl -X PUT http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{
    "exit_price": 44000
  }'
```

### 5. Check Portfolio
```bash
curl http://localhost:8000/api/v1/paper-trading/portfolio/1
```

---

## Troubleshooting Quick Fixes

### Port Already in Use
```bash
# Find and kill process on port
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :5173 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose restart postgres

# Test connection
psql -U trading_user -d trading_dashboard
```

### Dependencies Not Installing
```bash
# Backend
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### API Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Test health endpoint
curl http://localhost:8000/health
```

### CORS Errors
- Ensure frontend URL is in `CORS_ORIGINS` in `backend/app/main.py`
- Default: `http://localhost:5173`
- Restart backend after changes

---

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_dashboard
DEBUG=true
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
API_VERSION=v1
```

### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=10000
```

---

## Keyboard Shortcuts (Frontend)

- `Ctrl+Shift+D`: Open Vue DevTools
- `F12`: Browser DevTools
- `Ctrl+K`: Command palette (if configured)

---

## File Locations

| What | Location |
|------|----------|
| Frontend Code | `frontend/src/` |
| Backend Code | `backend/app/` |
| API Routes | `backend/app/api/` |
| Database Schema | `database/schema.sql` |
| API Documentation | `API_REFERENCE.md` |
| Setup Guide | `SETUP.md` |

---

## Git Commands

```bash
# Create feature branch
git checkout -b feature/your-feature

# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "feat: your message"

# Push
git push origin feature/your-feature

# View logs
git log --oneline -10
```

---

## Testing APIs

### With curl
```bash
# GET request
curl http://localhost:8000/api/v1/health

# POST request
curl -X POST http://localhost:8000/api/v1/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# PUT request
curl -X PUT http://localhost:8000/api/v1/endpoint/1 \
  -H "Content-Type: application/json" \
  -d '{"key": "new_value"}'
```

### With httpie
```bash
# Install: pip install httpie

http GET localhost:8000/api/v1/health
http POST localhost:8000/api/v1/endpoint key=value
```

### With Postman/Insomnia
1. Open Postman/Insomnia
2. Import from: http://localhost:8000/openapi.json
3. Start testing

---

## Performance Tips

1. **Frontend**: Use Vue DevTools Profiler tab
2. **Backend**: Check `/api/v1` endpoint timing
3. **Database**: Use EXPLAIN in PostgreSQL for slow queries
4. **Network**: Check browser Network tab in DevTools

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| README.md | Project overview & features |
| SETUP.md | Step-by-step setup instructions |
| API_REFERENCE.md | Complete API documentation |
| PROJECT_OVERVIEW.md | Architecture & structure |
| QUICK_REFERENCE.md | This file - quick lookups |

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill process or change port in docker-compose.yml |
| Port 5173 in use | Kill process or npm will prompt for alternate port |
| DB won't connect | Check DATABASE_URL, restart postgres, verify credentials |
| CORS error | Add frontend URL to CORS list, restart backend |
| Module not found | Activate venv, reinstall requirements.txt |
| npm install fails | Clear cache: `npm cache clean --force` |
| Charts not showing | Check TradingView chart-container div, verify data |
| API 404 errors | Check endpoint path, verify backend is running |

---

## Next Steps

1. ✅ Initialize git repo and commit initial code
2. ⬜ Set up CI/CD pipeline (GitHub Actions)
3. ⬜ Add authentication (JWT)
4. ⬜ Deploy to cloud (AWS/Heroku/DigitalOcean)
5. ⬜ Set up monitoring (Sentry, DataDog)
6. ⬜ Add more tests
7. ⬜ Integrate more exchanges

---

## Quick Links

- 📚 [README](README.md) - Full documentation
- 🚀 [SETUP](SETUP.md) - Getting started
- 📋 [API Docs](API_REFERENCE.md) - API endpoints
- 🏗️ [Overview](PROJECT_OVERVIEW.md) - Architecture
- 🔗 [Live API Docs](http://localhost:8000/docs) - Interactive
- 💾 [Database Schema](database/schema.sql) - DB structure

---

**Happy Coding! 🚀 Happy Trading! 📈**
