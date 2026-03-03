# Caddy Setup - Quick Start

## Summary of Changes

The project has been reconfigured to work with Caddy reverse proxy:

✅ **Port Changes** (to avoid conflicts):
- Backend: `8000` → `8001`
- Frontend: `5173` → `5174`
- Database: `5432` (unchanged, internal only)

✅ **Configuration Updates**:
- Frontend base path set to `/trading`
- API client updated to use `/trading/api`
- CORS configured to be flexible
- Vite proxy configured for dev

## Step 1: Add to Your Caddyfile

**Location**: Usually `/etc/caddy/Caddyfile`

Add this to your existing configuration:

```caddy
example.com {
    # Replace example.com with your actual domain

    # Frontend at /trading
    handle /trading* {
        uri strip_prefix /trading
        reverse_proxy localhost:5174
    }

    # API at /trading/api
    handle /trading/api* {
        uri strip_prefix /trading/api
        uri path_regexp ^/(.*)$ /api/$1
        reverse_proxy localhost:8001
    }

    # Your other services...
}
```

## Step 2: Test Caddy Config

```bash
caddy validate --config Caddyfile
```

## Step 3: Reload Caddy

```bash
# If using systemd
sudo systemctl reload caddy

# If using Docker
docker-compose -f your-caddy-compose.yml up -d

# If running directly
caddy reload --config Caddyfile
```

## Step 4: Start Trading Dashboard

```bash
cd /path/to/trading_dashboard
docker-compose up -d
```

## Step 5: Test It Works

Open in browser:
```
https://example.com/trading
```

Or test API:
```bash
curl https://example.com/trading/api/v1/health
```

## Port Mapping

These services will NOT be exposed on these ports directly:
- ❌ `localhost:5173` (was frontend)
- ❌ `localhost:8000` (was backend)

They run on:
- ✅ `localhost:5174` (frontend, internal only)
- ✅ `localhost:8001` (backend, internal only)

Access them through Caddy only:
- ✅ `https://example.com/trading` (frontend)
- ✅ `https://example.com/trading/api` (API)

## If You Have Conflicts

If services are still running on 5173 or 8000:

```bash
# Kill processes
lsof -i :5173 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or stop other Docker services
docker stop any_other_services
```

## Common Issues

### Can't access /trading
- Check Caddy is running: `systemctl status caddy`
- Reload Caddy: `sudo systemctl reload caddy`
- Verify backend is running: `docker-compose ps`

### 502 Bad Gateway
- Check backend running: `docker-compose logs backend`
- Check port 8001 is accessible: `curl localhost:8001/health`
- Check Caddyfile syntax: `caddy validate --config Caddyfile`

### Old ports still accessible
- Update docker-compose.yml ✅ (already done)
- Stop old services
- Rebuild containers: `docker-compose down && docker-compose up -d`

## What's Running

```
Your Domain (example.com)
        ↓
    [Caddy] - Reverse Proxy
        ↓
    ├─→ /trading → [Frontend:5174]
    └─→ /trading/api → [Backend:8001]
        ↓
    [PostgreSQL:5432] - Database (internal only)
```

## Production Environment

Update backend `.env`:

```env
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_dashboard
DEBUG=false
PRODUCTION_DOMAIN=https://example.com
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

Then restart:
```bash
docker-compose restart backend
```

## Next Steps

1. ✅ Check if ports 8001 and 5174 are free
2. ✅ Update your Caddyfile
3. ✅ Run `caddy validate --config Caddyfile`
4. ✅ Reload Caddy
5. ✅ Run `docker-compose up -d`
6. ✅ Visit `https://example.com/trading`

## Files Changed

- `docker-compose.yml` - Updated ports to 8001 and 5174
- `frontend/vite.config.js` - Set base path to /trading
- `frontend/src/api/client.js` - Updated API base URL to /trading/api/v1
- `backend/app/main.py` - Updated CORS configuration

## Reference Documentation

- **Detailed Setup**: See `CADDY_SETUP.md`
- **Troubleshooting**: See `CADDY_SETUP.md` - Troubleshooting section
- **Docker Compose**: See `docker-compose.yml`
- **Main Docs**: See `README.md`

---

**That's it! 🎉 Your Trading Dashboard is now ready for production with Caddy!**
