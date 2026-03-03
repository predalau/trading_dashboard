# Architecture Diagram

## Network Flow with Caddy

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Server                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Browser (https://example.com/trading)                         │
│         ↓                                                             │
│    [Caddy Reverse Proxy]  ← Listens on 80/443                       │
│         ↓                                                             │
│    ┌────────────────────────────────────────┐                       │
│    │  URL Routing                           │                       │
│    ├────────────────────────────────────────┤                       │
│    │ /trading           → localhost:5174    │                       │
│    │ /trading/api/*     → localhost:8001    │                       │
│    │ (other services)   → other ports       │                       │
│    └────────────────────────────────────────┘                       │
│         ↓              ↓                                              │
│    ┌──────────┐   ┌────────────┐                                    │
│    │ Frontend │   │  Backend   │                                    │
│    │ Vue 3    │   │  FastAPI   │                                    │
│    │:5174     │   │  :8001     │                                    │
│    └──────────┘   └────────────┘                                    │
│         ↓              ↓                                              │
│    [Assets]      ┌────────────┐                                     │
│    [HTML/JS]     │ PostgreSQL │                                     │
│    [CSS]         │ Database   │                                     │
│                  │ :5432      │                                     │
│                  │(internal)  │                                     │
│                  └────────────┘                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Service Interactions

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Docker Network (Internal)                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │ Frontend Container (trading_dashboard_ui)                   │  │
│   │ ├─ Vite Dev Server                                          │  │
│   │ ├─ Port: 5173 (internal)                                    │  │
│   │ ├─ Exposed: localhost:5174 (external)                       │  │
│   │ └─ Serves: /trading route                                   │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │ Backend Container (trading_dashboard_api)                   │  │
│   │ ├─ FastAPI + Uvicorn                                        │  │
│   │ ├─ Port: 8000 (internal)                                    │  │
│   │ ├─ Exposed: localhost:8001 (external)                       │  │
│   │ ├─ Endpoints: /api/v1/*                                     │  │
│   │ ├─ Services:                                                │  │
│   │ │  ├─ Paper Trading API                                     │  │
│   │ │  ├─ Market Data API                                       │  │
│   │ │  └─ User Management API                                   │  │
│   │ └─ Depends on: PostgreSQL                                   │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                       │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │ PostgreSQL Container (trading_dashboard_db)                 │  │
│   │ ├─ Database: trading_dashboard                              │  │
│   │ ├─ Port: 5432 (internal only)                               │  │
│   │ ├─ Tables:                                                  │  │
│   │ │  ├─ users                                                 │  │
│   │ │  ├─ paper_trading_accounts                                │  │
│   │ │  ├─ trades                                                │  │
│   │ │  ├─ orders                                                │  │
│   │ │  ├─ market_data                                           │  │
│   │ │  └─ portfolio_snapshots                                   │  │
│   │ └─ Persisted: Docker volume (postgres_data)                │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## API Request Flow Example

```
Browser Request:
https://example.com/trading/api/v1/paper-trading/accounts

                    ↓
            [Caddy Reverse Proxy]
        (receives full request path)
                    ↓
            Match: /trading/api*
                    ↓
        ┌─ Strip prefix: /trading/api
        └─ Rewrite path: /api/$1 (adds back /api)
                    ↓
            Send to: localhost:8001/api/v1/paper-trading/accounts
                    ↓
            [FastAPI Backend]
        (receives /api/v1/paper-trading/accounts)
                    ↓
        Route matches: /api/v1/paper-trading -> router prefix
                    ↓
        Handler: POST /accounts or GET /accounts
                    ↓
        Query Database
                    ↓
        Return JSON Response
                    ↓
            [Caddy] (returns response)
                    ↓
            Browser (displays data)
```

## Frontend Development Flow

```
Local Development (Before Caddy):
http://localhost:5173
        ↓
    [Vite Dev Server]
        ↓
    Hot Module Replacement (HMR)
        ↓
    Proxy: /trading/api → localhost:8000/api
        ↓
    [FastAPI Backend]


Production (With Caddy):
https://example.com/trading
        ↓
    [Caddy Reverse Proxy]
        ↓
    Strip /trading prefix
        ↓
    [Frontend Build]
    (/index.html, /assets/*, etc)
        ↓
    User sees: https://example.com/trading
```

## Data Flow for Paper Trading

```
┌─────────────────┐
│ User Browser    │
│ (Dashboard)     │
└────────┬────────┘
         │
         │ POST: /trading/api/v1/paper-trading/trades
         ↓
    [Caddy] → Strip /trading/api → /api
         │
         ↓
    [FastAPI] → /api/v1/paper-trading/trades
         │
         ├─ Validate input (Pydantic)
         │
         ├─ Check account balance
         │
         ├─ Create Trade record
         │
         ↓
    [PostgreSQL]
    INSERT INTO trades (...)
         │
         ├─ Update account balance
         │
         ↓
    [PostgreSQL]
    UPDATE paper_trading_accounts SET...
         │
         ↓
    Return JSON with Trade ID
         │
         ↓
    [Caddy] → Add /trading prefix back
         │
         ↓
    [Browser] → Update UI, show trade
```

## Ports Reference

| Port | Service | Exposed | Access Method |
|------|---------|---------|----------------|
| 5432 | PostgreSQL | ❌ No | Internal Docker only |
| 5174 | Frontend (Docker Host) | ✅ Yes | localhost:5174 (dev) |
| 5173 | Frontend (Container) | ❌ No | Docker internal |
| 8001 | Backend (Docker Host) | ✅ Yes | localhost:8001 (dev) |
| 8000 | Backend (Container) | ❌ No | Docker internal |
| 80 | Caddy HTTP | ✅ Yes | example.com |
| 443 | Caddy HTTPS | ✅ Yes | example.com (main) |

## Environment Variables

```
Backend (.env):
├─ DATABASE_URL (PostgreSQL connection)
├─ DEBUG (true/false)
├─ BINANCE_API_KEY
├─ BINANCE_API_SECRET
└─ PRODUCTION_DOMAIN (for CORS)

Frontend (.env.local):
├─ VITE_API_BASE_URL (/trading/api/v1)
└─ VITE_API_TIMEOUT (10000ms)

Caddy (Caddyfile):
├─ Domain name (example.com)
├─ Reverse proxy targets (localhost:5174, localhost:8001)
└─ URL rewriting rules
```

## Scalability Considerations

### Current Setup
```
Single Server
├─ Caddy (reverse proxy)
├─ Frontend (Vite, static files)
├─ Backend (FastAPI, async)
└─ Database (PostgreSQL)
```

### Horizontal Scaling
```
Multiple Backend Servers:
                Caddy (Load Balancer)
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
    Backend 1    Backend 2    Backend 3
        │             │             │
        └─────────────┼─────────────┘
                      ↓
              PostgreSQL (Shared)
```

### Vertical Scaling
```
Current: Single Docker Compose
Future:
├─ Kubernetes (cloud-native)
├─ Separate database server
├─ Separate cache (Redis)
├─ Message queue (RabbitMQ)
└─ WebSocket server for real-time updates
```

## Security Architecture

```
User → HTTPS (encrypted) → Caddy (TLS termination)
                               ↓
                        HTTP (internal network)
                               ↓
                        Backend (no TLS needed)
```

Benefits:
- ✅ HTTPS/TLS handled by Caddy
- ✅ Backend on private network
- ✅ Only Caddy exposed to internet
- ✅ Database internal only

---

**Note**: All internal services communicate over the Docker network, which is isolated from the host network. Only Caddy listens on public ports (80/443).
