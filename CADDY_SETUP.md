# Caddy Reverse Proxy Setup Guide

This guide explains how to set up Caddy to serve the Trading Dashboard at `[base_url]/trading` and the API at `[base_url]/trading/api`.

## Overview

- **Frontend**: Served at `https://example.com/trading`
- **API**: Served at `https://example.com/trading/api/v1/...`
- **Backend Port**: `8001` (internal, not exposed)
- **Frontend Port**: `5174` (internal, not exposed)
- **Database Port**: `5432` (internal, not exposed)

## Port Changes

The Docker Compose file has been updated to use different internal ports to avoid conflicts:
- Frontend: `5174` (was `5173`)
- Backend: `8001` (was `8000`)
- Database: `5432` (unchanged, internal only)

## Caddy Configuration

### Basic Setup (Single Domain)

If you have a domain like `example.com` and want to host the dashboard at `/trading`:

```caddy
example.com {
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
}
```

### Add to Existing Caddyfile

If you already have a Caddyfile with other services:

```caddy
example.com {
    # Your existing services...

    # Trading Dashboard
    handle /trading* {
        uri strip_prefix /trading
        reverse_proxy localhost:5174
    }

    handle /trading/api* {
        uri strip_prefix /trading/api
        uri path_regexp ^/(.*)$ /api/$1
        reverse_proxy localhost:8001
    }

    # More services...
}
```

### Subdomain Setup (Alternative)

If you prefer to use a subdomain instead:

```caddy
trading.example.com {
    reverse_proxy localhost:5174

    handle /api* {
        reverse_proxy localhost:8001
    }
}
```

## Implementation Steps

### 1. Update Your Caddyfile

**Location**: Usually at `/etc/caddy/Caddyfile` or your Caddy config directory.

Add the trading dashboard configuration from above to your existing Caddyfile.

### 2. Test Caddy Configuration

```bash
# Validate Caddy syntax
caddy validate --config Caddyfile

# Or test with caddy fmt
caddy fmt --overwrite Caddyfile
```

### 3. Reload Caddy

```bash
# If Caddy is running as a service
sudo systemctl reload caddy

# If Caddy is running in Docker
docker-compose -f your-caddy-compose.yml up -d

# If running Caddy manually
caddy reload --config Caddyfile
```

### 4. Start Trading Dashboard Services

```bash
cd /path/to/trading_dashboard
docker-compose up -d
```

### 5. Verify Everything Works

```bash
# Test frontend
curl -I https://example.com/trading

# Test API health check
curl https://example.com/trading/api/v1/health

# Check logs
docker-compose logs -f
```

## Environment Variable Setup

Update the backend `.env` file to include your production domain:

```env
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_dashboard
DEBUG=false
PRODUCTION_DOMAIN=https://example.com
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

Then restart the backend:
```bash
docker-compose restart backend
```

## URL Mapping Examples

After setup, here's how URLs are mapped:

| User Access | Caddy Receives | Backend Sees | Service |
|-------------|---|---|---|
| `/trading` | `/trading` | `/` | Frontend (5174) |
| `/trading/index.html` | `/trading/index.html` | `/index.html` | Frontend (5174) |
| `/trading/api/v1/health` | `/trading/api/v1/health` | `/api/v1/health` | Backend (8001) |
| `/trading/api/v1/paper-trading/...` | `/trading/api/v1/paper-trading/...` | `/api/v1/paper-trading/...` | Backend (8001) |

## Troubleshooting

### "Connection refused" at localhost:5174 or localhost:8001

**Problem**: Services aren't running
**Solution**:
```bash
docker-compose ps
docker-compose logs backend frontend
docker-compose up -d
```

### 404 on `/trading` frontend

**Problem**: Frontend not being served correctly
**Solution**:
1. Check Caddy is routing to port 5174:
   ```bash
   curl -v http://localhost:5174
   ```
2. Check Caddy config:
   ```bash
   caddy validate --config Caddyfile
   ```
3. Reload Caddy:
   ```bash
   sudo systemctl reload caddy
   ```

### 502 Bad Gateway errors

**Problem**: Caddy can't reach backend
**Solution**:
1. Verify backend is running:
   ```bash
   docker ps | grep trading_dashboard_api
   docker-compose logs backend
   ```
2. Test direct connection:
   ```bash
   curl http://localhost:8001/health
   ```
3. Check firewall isn't blocking localhost:8001

### API calls still hitting old port (8000 or 5173)

**Problem**: Browser cached old configuration
**Solution**:
1. Clear browser cache
2. Hard refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
3. Check browser DevTools Network tab to verify correct URLs

### CORS errors in browser console

**Problem**: API calls being blocked by CORS
**Solution**:
1. Ensure `PRODUCTION_DOMAIN` env var is set in backend:
   ```bash
   docker-compose exec backend env | grep DOMAIN
   ```
2. Restart backend:
   ```bash
   docker-compose restart backend
   ```
3. Check that your domain matches exactly (include protocol):
   ```env
   PRODUCTION_DOMAIN=https://example.com
   # NOT http:// if using HTTPS
   # NOT with trailing slash
   ```

## Advanced: Multiple Environments

If you have dev, staging, and production:

```caddy
# Development
dev.example.com {
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

# Staging
staging.example.com {
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

# Production
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

## Monitoring

### Check Caddy logs
```bash
# If Caddy is a systemd service
sudo journalctl -u caddy -f

# If Caddy is in Docker
docker-compose logs -f caddy

# Check specific service
sudo tail -f /var/log/caddy/access.log
```

### Monitor Docker services
```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Test endpoints
```bash
# Frontend health (should load page)
curl -I https://example.com/trading

# API health (should return JSON)
curl https://example.com/trading/api/v1/health

# Create test trade
curl -X POST https://example.com/trading/api/v1/paper-trading/accounts \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "account_name": "Test", "initial_balance": 10000}'
```

## Common Caddy Directives Reference

```caddy
# Route matching
handle /path* { ... }      # Matches /path, /path/*, /path123, etc.
handle_path /path { ... }  # Matches /path/*, removes /path from request

# URI manipulation
uri strip_prefix /prefix   # Removes prefix from path
uri path_regexp ^/(.*)$ /prefix/$1  # Regex replace

# Reverse proxy
reverse_proxy localhost:8000 {
    header_uri -X-Forwarded-Path  # Remove headers
    header_down -X-Forwarded-Path
}

# Headers
header Connection close             # Set header
header -Server                      # Remove header
```

## Security Considerations

1. **Always use HTTPS** in production
2. **Restrict access** to admin panels if needed:
   ```caddy
   handle /trading/admin* {
       @allowed remote_ip 203.0.113.0/24
       reject
   }
   ```
3. **Rate limiting** (Caddy v2.6+):
   ```caddy
   rate_limit /trading/api/v1/* 100r/h
   ```
4. **Basic auth** (if needed):
   ```caddy
   handle /trading* {
       basicauth /trading/* {
           user HashedPassword
       }
   }
   ```

## Performance Tips

1. **Enable compression** (Caddy does this by default for HTML/JSON/JS)
2. **Use caching headers** for static assets
3. **Monitor resource usage**:
   ```bash
   docker-compose stats
   ```
4. **Use separate domains** if you have many services

## Next Steps

1. ✅ Update `docker-compose.yml` (already done)
2. ✅ Update frontend config (already done)
3. Add Caddy configuration to your Caddyfile
4. Test the configuration
5. Monitor logs for errors
6. Adjust as needed

## Support

If you encounter issues:
1. Check Caddy logs: `sudo journalctl -u caddy -f`
2. Check container logs: `docker-compose logs`
3. Test direct connection to services: `curl localhost:5174`, `curl localhost:8001`
4. Verify Caddy syntax: `caddy validate --config Caddyfile`
5. Check firewall rules

---

**Happy Trading with Caddy! 🚀**
