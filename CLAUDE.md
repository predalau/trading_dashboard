# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

### Development (Docker)
```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop services
docker-compose logs -f backend    # View backend logs
docker-compose logs -f frontend   # View frontend logs
```

### Frontend Development
```bash
cd frontend
npm install                       # Install dependencies
npm run dev                       # Start Vite dev server (http://localhost:5173)
npm run build                     # Build for production
npm run lint                      # Lint and fix code
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload  # Start dev server (http://localhost:8000)
pytest tests/                     # Run backend tests
```

### Reverse Proxy (Caddy)
```bash
docker logs caddy                 # View Caddy logs
docker exec caddy caddy reload --config /etc/caddy/Caddyfile  # Reload config
curl -v https://preda.home.ro/trading  # Test HTTPS access
```

---

## Architecture Overview

### Three-Tier Setup
```
User Browser (https://preda.home.ro/trading)
    ↓
Caddy Reverse Proxy (TLS termination)
    ├─ /trading → Frontend (Vue 3, localhost:5173)
    └─ /trading/api/* → Backend (FastAPI, localhost:8000)
    ↓
PostgreSQL Database (internal Docker network)
```

**Key Points:**
- **Frontend** built with Vite, served at `/trading/` with `base: '/trading/'` in vite.config.js
- **Backend** FastAPI app receives requests at `/trading/api/v1/*` which Caddy rewrites to `/api/v1/*`
- **Caddy** (in `/home/preda/docker/conf/Caddyfile`) handles all public HTTP/HTTPS and routes internally
- **Database** PostgreSQL runs in Docker on internal network only (no external access)

### Data Flow for API Requests
```
Browser: GET /trading/api/v1/paper-trading/accounts
    ↓ [Caddy rewrites path: strip /trading/api, add back /api]
FastAPI: GET /api/v1/paper-trading/accounts
    ↓ [Router prefix: /api/v1]
Handler: GET /paper-trading/accounts
    ↓ [Query database]
PostgreSQL: SELECT * FROM paper_trading_accounts
```

---

## Project Structure

### Frontend (`/frontend`)
- **`src/pages/`** - Three main pages: Home.vue, Dashboard.vue, Trades.vue
- **`src/components/ChartComponent.vue`** - TradingView Lightweight Charts integration
- **`src/stores/trading.js`** - Pinia state management for trading data
- **`src/api/client.js`** - Axios HTTP client configured for `/trading/api/v1` base URL
- **`src/style.css`** - Global styles with custom glass-morphism effects (dark purple theme)
- **`vite.config.js`** - Critical: `base: '/trading/'` tells Vite to serve from `/trading/` path
- **`tailwind.config.js`** - Color palette defined here (dark theme with purple accents)

**Key Frontend Patterns:**
- Routes are defined in `src/router/index.js`
- API calls use `client.js` which prefixes all requests with `/trading/api/v1`
- Pinia stores (`stores/trading.js`) handle global state
- All CSS uses Tailwind or custom CSS with no JavaScript animations (performance)

### Backend (`/backend`)
- **`app/main.py`** - FastAPI app setup, CORS, route registration
- **`app/api/`** - Three endpoint modules:
  - `paper_trading.py` - 6 endpoints for trading accounts, trades, portfolio
  - `market_data.py` - 4 endpoints for prices, candlesticks, symbols
  - `user.py` - 2 endpoints for user registration/profile
- **`app/services/`** - Business logic layer:
  - `trading_service.py` - Account management, trade execution, P&L calculation
  - `market_service.py` - Binance API integration
- **`app/models.py`** - SQLAlchemy ORM models (User, PaperTradingAccount, Trade, etc.)
- **`app/database.py`** - PostgreSQL connection setup
- **`requirements.txt`** - Python dependencies

**Key Backend Patterns:**
- All endpoints return JSON with status codes
- Pydantic models validate input (see endpoint docstrings)
- Async/await throughout (FastAPI + SQLAlchemy)
- Market data cached where possible (Binance API rate limits)
- Services handle business logic, routes just validate and call services

### Database (`/database`)
- **`schema.sql`** - 7 tables: users, paper_trading_accounts, trades, orders, market_data, portfolio_snapshots, (plus audit fields)
- Indexes on: symbol, timestamp, account_id, user_id (important for query performance)

### Reverse Proxy (`/home/preda/docker/conf/Caddyfile`)
- **Caddy** serves as TLS terminator (handles HTTPS)
- Routes `/trading/*` to frontend, `/trading/api/*` to backend
- **Path rewriting critical**:
  - Line 68: `redir /trading /trading/` - redirect trailing slash
  - Line 69: `reverse_proxy /trading/* investhor_frontend:5173` - proxies full path (doesn't strip prefix)
  - Line 74-78: `/trading/api/*` handler strips prefix and rewrites to `/api/$1`
- **Do NOT use `handle_path` for frontend** - it strips the path prefix which causes redirect loops

---

## Common Development Tasks

### Add a New API Endpoint
1. Create handler in `backend/app/api/` (choose which file based on feature)
2. Add Pydantic models for request/response validation
3. Register route in handler: `@router.get("/path")` or `@router.post("/path")`
4. Business logic goes in `backend/app/services/`
5. Route is auto-registered in `main.py` via `app.include_router()`

Example: `backend/app/api/paper_trading.py` shows the pattern.

### Update Color Scheme
- **Tailwind colors**: Edit `frontend/tailwind.config.js` - `accent` section
- **Custom CSS**: Edit `frontend/src/style.css` - look for `rgba()` color values in glass-effect, cards, buttons
- **Component colors**: Search Vue files for `text-purple-*`, `border-purple-*`, `bg-purple-*` Tailwind classes

Current theme: Dark base with **purple/violet** accents (`#a78bfa` primary, `#7c3aed` secondary)

### Fix Caddy Redirect Issues
- **Always test with curl**: `docker exec caddy curl -v http://investhor_frontend:5173/path`
- **Check logs**: `docker logs caddy 2>&1 | grep -i error`
- **Key rules**:
  - Use `reverse_proxy /path/* service:port` for simple forwarding (doesn't strip prefix)
  - Use `handle_path /path/*` only when service needs prefix stripped
  - Frontend needs full `/trading/` path (configured in vite.config.js)
  - API backend receives paths with `/trading/api/` stripped (rewrites to `/api/`)

### Database Queries During Development
```bash
# SSH into PostgreSQL container
docker exec -it investhor_db psql -U $DB_USER -d trading_dashboard

# Common queries
SELECT * FROM users;
SELECT * FROM paper_trading_accounts;
SELECT * FROM trades ORDER BY created_at DESC LIMIT 10;
```

---

## Frontend Details

### Vue Router Setup (`src/router/index.js`)
- Routes: `/` (home), `/dashboard`, `/trades`
- All routes have base path `/trading/` configured
- No authentication guards (yet)

### API Client (`src/api/client.js`)
```javascript
const client = axios.create({
  baseURL: '/trading/api/v1',  // CRITICAL: matches Caddy rewrite
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})
```
All API calls use this client, so requests automatically get `/trading/api/v1` prefix.

### Pinia Store (`src/stores/trading.js`)
- Manages trading data state globally
- Accesses API via the `client` imported from `api/client.js`
- Components dispatch actions, store handles API calls

### Styling System
- **Tailwind**: Configured in `tailwind.config.js`, used for layout and responsive design
- **Custom CSS**: `style.css` for complex effects (glass-morphism, card styling, animations)
- **Color Palette**: Edit `tailwind.config.js` `extend.colors.accent` to change theme colors
- **No JS Animations**: All animations are pure CSS (`@keyframes fadeIn`, `slideUp`) for performance

---

## Backend Details

### FastAPI Route Registration
All endpoints are prefixed with `/api/v1`:
```python
# backend/app/main.py
app.include_router(paper_trading.router, prefix="/api/v1")
app.include_router(market_data.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
```

So `@router.post("/paper-trading/accounts")` becomes `/api/v1/paper-trading/accounts`

### Database Models
- Each model in `models.py` is a SQLAlchemy ORM class
- Foreign keys link tables together (Trade.account_id → PaperTradingAccount.id)
- All models have `created_at`, `updated_at` audit fields
- Enums for trade_type (BUY/SELL), trade_status (OPEN/CLOSED)

### Services Layer
- `trading_service.py`: Account creation, trade execution, P&L calculation, portfolio snapshots
- `market_service.py`: Binance API wrapper, price lookups, candlestick data

Always call services from routes, never query database directly in route handlers.

### Testing
```bash
cd backend
pytest tests/ -v                    # Run all tests
pytest tests/test_api.py::test_foo -v  # Run specific test
pytest tests/ -k "paper_trading"    # Run tests matching keyword
```

---

## Deployment & Production Considerations

### Frontend Build
```bash
cd frontend
npm run build  # Creates dist/ folder with optimized production build
```

Output is static files ready to be served by any web server (Caddy, nginx, etc.)

### Backend Production
- Set `DEBUG=false` in `.env`
- Use production PostgreSQL (not Docker container)
- Configure CORS origins properly in `main.py`
- Use gunicorn/Uvicorn with multiple workers: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`
- Set up monitoring/logging
- Use environment variables for all secrets (API keys, database URLs)

### Caddy Configuration
- TLS certificates auto-managed by Caddy (uses Let's Encrypt)
- Caddyfile syntax: http/https blocks with matchers and handlers
- Always reload instead of restart: `caddy reload --config /etc/caddy/Caddyfile`
- Test config before deploying: `caddy validate --config /etc/caddy/Caddyfile`

---

## Debugging Tips

### "Too Many Redirects" Error
- **Frontend issue**: Check that `vite.config.js` has `base: '/trading/'`
- **Caddy issue**: Use `reverse_proxy /trading/*` (not `handle_path`) for frontend - the frontend needs full path
- **Test**: `docker exec caddy curl -v http://investhor_frontend:5173/trading/` should return 200 with HTML

### API 404 Errors
- Check route prefix: requests at `/trading/api/v1/...` should reach backend
- Verify `app/main.py` includes all routers
- Check route decorator in handler: `@router.post("/path")` → full path is `POST /api/v1/path`
- Use FastAPI Swagger at `http://localhost:8000/docs` to test endpoints

### CORS Errors
- Check `main.py` CORS configuration
- Allowed origin should include frontend URL during dev: `http://localhost:5173`, `http://localhost:5174`, `https://preda.home.ro`
- During dev, check vite.config.js proxy settings for `/trading/api` → backend mapping

### Database Connection Errors
- Verify PostgreSQL container is running: `docker ps | grep investhor_db`
- Check `DATABASE_URL` in `.env`
- Verify credentials match docker-compose.yml environment variables
- Test connection: `docker exec investhor_db psql -U $DB_USER -c "SELECT 1"`

### Port Conflicts
When containers won't start due to port already in use:
```bash
docker-compose down
docker volume prune  # Remove old volumes if needed
docker-compose up -d
```

---

## File Checklist for Common Changes

| Change Type | Files to Modify |
|---|---|
| **Add API Endpoint** | `backend/app/api/*.py`, `backend/app/services/*.py`, `backend/app/models.py` (if new data) |
| **Add Database Table** | `database/schema.sql`, `backend/app/models.py` |
| **Change Color Scheme** | `frontend/tailwind.config.js`, `frontend/src/style.css`, `frontend/src/App.vue`, `frontend/src/pages/*.vue` |
| **Add Frontend Page** | `frontend/src/pages/NewPage.vue`, `frontend/src/router/index.js` |
| **Fix Caddy Routes** | `/home/preda/docker/conf/Caddyfile`, then `docker exec caddy caddy reload...` |
| **Update Dependencies** | `frontend/package.json` (npm) or `backend/requirements.txt` (pip) |
| **Environment Variables** | `backend/.env`, `frontend/.env.local` |

---

## Key Design Decisions

1. **Vite for Frontend**: Fast builds, hot module replacement, modern tooling
2. **FastAPI for Backend**: Async-first, automatic Swagger docs, excellent performance
3. **PostgreSQL**: Relational database for financial data consistency
4. **Docker Compose**: One-command development environment
5. **Caddy as Reverse Proxy**: Automatic HTTPS/TLS, simple configuration, reliable
6. **Pinia for State**: Modern Vue state management (simpler than Vuex)
7. **TradingView Charts**: Industry-standard charting library (performant, feature-rich)
8. **SQLAlchemy ORM**: Type-safe database queries with Python classes

---

## Important URLs

| URL | Purpose | Port |
|---|---|---|
| http://localhost:5173 | Frontend dev server | 5173 |
| http://localhost:8000 | Backend API | 8000 |
| http://localhost:8000/docs | FastAPI Swagger UI | 8000 |
| http://localhost:8000/redoc | FastAPI ReDoc docs | 8000 |
| https://preda.home.ro/trading | Production frontend (requires Caddy) | 443 |
| https://preda.home.ro/trading/api/v1 | Production API (requires Caddy) | 443 |

---

## References

- **Frontend**: See `frontend/` folder and README.md for detailed Vue/Vite info
- **Backend**: See `backend/` folder and README.md for detailed FastAPI info
- **Architecture**: See `ARCHITECTURE.md` for network diagrams
- **API Endpoints**: See `API_REFERENCE.md` for complete endpoint documentation
- **Setup**: See `SETUP.md` for step-by-step development setup
- **Deployment**: See `docker-compose.yml` for containerization config
