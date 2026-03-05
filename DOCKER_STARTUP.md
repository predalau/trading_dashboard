# 🛡️ InvesThor - Docker Startup Guide

Welcome to **InvesThor** - The Viking Trading Warrior! ⚔️⚡

This guide will help you launch your trading empire using Docker.

## Prerequisites

- Docker & Docker Compose installed
- Port 5174 and 8001 available (or adjust in docker-compose.yml)
- Git with SSH configured (for pulling code)

**Check if Docker is installed:**
```bash
docker --version
docker-compose --version
```

---

## Quick Start (5 minutes)

### 1. Clone the Repository
```bash
git clone git@github.com:predalau/trading_dashboard.git
cd trading_dashboard
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Check If Everything Started
```bash
docker-compose ps
```

**Expected output:**
```
NAME                 STATUS
investhor_frontend   Up 2 minutes
investhor_backend    Up 2 minutes
investhor_db         Up 2 minutes
```

### 4. Access InvesThor
- **Frontend**: http://localhost:5174
- **API Docs**: http://localhost:8001/docs

---

## Container Names (Updated for InvesThor)

Your containers are now named with Viking honor:

```
⚔️ investhor_frontend    - Vue 3 Trading Dashboard
🛡️ investhor_backend     - FastAPI Backend Server
💾 investhor_db          - PostgreSQL Database
```

Check running containers:
```bash
docker ps | grep investhor
```

---

## Docker Compose Commands

### Start Services
```bash
# Start all containers in background
docker-compose up -d

# Start with logs visible
docker-compose up

# Start specific service
docker-compose up -d investhor_backend
```

### Stop Services
```bash
# Stop all containers
docker-compose stop

# Stop specific container
docker-compose stop investhor_frontend

# Stop and remove containers
docker-compose down
```

### View Logs
```bash
# View all logs
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# View specific service logs
docker-compose logs -f investhor_backend
docker-compose logs -f investhor_frontend
docker-compose logs -f investhor_db
```

### Rebuild Containers
```bash
# Rebuild images
docker-compose build

# Rebuild and start
docker-compose up -d --build

# Rebuild specific service
docker-compose build investhor_backend
```

### Access Container Shell
```bash
# Access backend container
docker-compose exec investhor_backend sh

# Access frontend container
docker-compose exec investhor_frontend sh

# Access database container
docker-compose exec investhor_db psql -U trading_user -d trading_dashboard
```

---

## Verify Everything Works

### 1. Check Container Status
```bash
docker-compose ps
```

All containers should show `Up` status.

### 2. Test Frontend
```bash
curl -I http://localhost:5174
# Should return HTTP 200
```

### 3. Test Backend API
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy"}
```

### 4. Visit Dashboard in Browser
Open: **http://localhost:5174**

You should see the InvesThor logo and Viking-themed interface! ⚔️

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs investhor_backend

# Common issues:
# - Port already in use: Change port in docker-compose.yml
# - Database not ready: Wait 10 seconds and retry
# - Out of disk space: docker system prune
```

### Port already in use
```bash
# Find what's using port 5174
lsof -i :5174

# Find what's using port 8001
lsof -i :8001

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
# frontend: 5175:5173
# backend: 8002:8000
```

### Database connection error
```bash
# Check database logs
docker-compose logs investhor_db

# Restart database
docker-compose restart investhor_db

# Or reset everything
docker-compose down -v
docker-compose up -d
```

### Frontend not loading
```bash
# Check frontend logs
docker-compose logs investhor_frontend

# Rebuild frontend
docker-compose up -d --build investhor_frontend

# Clear browser cache: Ctrl+Shift+Delete (Chrome)
```

### API calls failing (CORS errors)
```bash
# Check backend CORS config
docker-compose logs investhor_backend

# Restart backend
docker-compose restart investhor_backend
```

---

## File Structure in Containers

### Frontend Container (investhor_frontend)
```
/app (Volume mounted)
├── src/
│   ├── pages/
│   ├── components/
│   └── stores/
├── index.html
├── package.json
└── vite.config.js
```

### Backend Container (investhor_backend)
```
/app (Volume mounted)
├── app/
│   ├── api/
│   ├── services/
│   ├── models.py
│   └── main.py
├── requirements.txt
└── Dockerfile
```

### Database Container (investhor_db)
```
PostgreSQL 16
Database: trading_dashboard
Port: 5432 (internal only)
```

---

## Environment Variables

### Backend (.env file)
```env
DATABASE_URL=postgresql://trading_user:trading_password@investhor_db:5432/trading_dashboard
DEBUG=true
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

### Frontend (automatic via Vite)
```
Base URL: /trading
API Base: /trading/api/v1 (when behind Caddy)
Local API: http://localhost:8001/api/v1 (direct access)
```

---

## Development Workflow

### Make Changes to Frontend
1. Edit files in `frontend/src/`
2. Changes auto-reload in browser (HMR)
3. Check http://localhost:5174

### Make Changes to Backend
1. Edit files in `backend/app/`
2. Server auto-reloads with `--reload` flag
3. Check http://localhost:8001/docs

### Database Changes
1. Edit schema in `database/schema.sql`
2. Restart database: `docker-compose restart investhor_db`
3. Or reset: `docker-compose down -v && docker-compose up -d`

---

## Performance Monitoring

### View Resource Usage
```bash
# See CPU/Memory for each container
docker-compose stats

# Exit: Ctrl+C
```

### View Real-time Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow with timestamp
docker-compose logs -f --timestamps
```

### Check Disk Usage
```bash
# See Docker disk usage
docker system df

# Clean up unused data
docker system prune
```

---

## Data Persistence

Your data is stored in Docker volumes:

```bash
# List volumes
docker volume ls | grep investhor

# Backup database
docker-compose exec investhor_db pg_dump -U trading_user trading_dashboard > backup.sql

# Restore database
docker-compose exec -T investhor_db psql -U trading_user trading_dashboard < backup.sql
```

---

## Advanced: Multiple Environments

### Development
```bash
docker-compose up -d
# Includes --reload, debug mode, volumes mounted
```

### Production-like
```bash
# Edit docker-compose.yml:
# - DEBUG=false
# - Remove volume mounts
# - Remove --reload flag

docker-compose -f docker-compose.prod.yml up -d
```

---

## With Caddy Reverse Proxy

If using Caddy (see CADDY_SETUP.md):

### Caddy Configuration
```caddy
example.com {
    handle /trading* {
        uri strip_prefix /trading
        reverse_proxy localhost:5174
    }

    handle /trading/api* {
        uri strip_prefix /trading/api
        uri path_regexp ^/(.*)$ /api/$1
        reverse_proxy localhost:8001
    }
}
```

### Access via Caddy
- Frontend: https://example.com/trading
- API Docs: https://example.com/trading/api/v1/docs

---

## Complete Command Reference

```bash
# ====== START / STOP ======
docker-compose up -d                    # Start all
docker-compose down                     # Stop all
docker-compose restart                  # Restart all

# ====== LOGS ======
docker-compose logs                     # View all logs
docker-compose logs -f investhor_backend # Follow backend logs
docker-compose logs --tail 100          # Last 100 lines

# ====== STATUS ======
docker-compose ps                       # Container status
docker-compose top investhor_backend    # Running processes
docker-compose stats                    # Resource usage

# ====== BUILD / REBUILD ======
docker-compose build                    # Build images
docker-compose up -d --build            # Rebuild and start
docker-compose build --no-cache         # Force rebuild

# ====== DATABASE ======
docker-compose exec investhor_db psql -U trading_user -d trading_dashboard
# Then: SELECT * FROM trades;

# ====== SHELL ACCESS ======
docker-compose exec investhor_backend sh
docker-compose exec investhor_frontend sh

# ====== CLEANUP ======
docker-compose down                     # Stop containers
docker-compose down -v                  # Stop + remove volumes (⚠️ data loss!)
docker system prune                     # Remove unused data
```

---

## FAQ

**Q: How do I change ports?**
A: Edit `docker-compose.yml` - change the first port number:
```yaml
frontend:
  ports:
    - "5175:5173"  # Changed from 5174
backend:
  ports:
    - "8002:8000"  # Changed from 8001
```

**Q: How do I add environment variables?**
A: Create/edit `.env` file in the project root:
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

**Q: Can I run this on a VPS/Server?**
A: Yes! See CADDY_SETUP.md for production deployment with reverse proxy.

**Q: How do I backup my data?**
A:
```bash
# Backup database
docker-compose exec investhor_db pg_dump -U trading_user trading_dashboard > backup.sql

# Backup entire volumes
docker run --rm -v investhor_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/db_backup.tar.gz -C /data .
```

**Q: My container keeps crashing**
A: Check logs with `docker-compose logs -f investhor_backend` and look for errors.

---

## Next Steps

1. ✅ Run `docker-compose up -d`
2. ✅ Open http://localhost:5174
3. ✅ Create a paper trading account
4. ✅ Place your first trade!
5. ✅ Read CADDY_SETUP.md for production deployment

---

## Support

If issues arise:
1. Check logs: `docker-compose logs`
2. Restart: `docker-compose restart`
3. Reset: `docker-compose down -v && docker-compose up -d`
4. Check port conflicts: `lsof -i :5174 && lsof -i :8001`

---

**Valhalla awaits! May your trades be victorious! ⚔️🛡️⚡**
