# 🛡️ InvesThor Security Guide

## Credentials & Environment Variables

### Development Setup (What You Just Did! ✅)

We've set up a secure credentials system using `.env.docker`:

#### 1. The `.env.docker` File
```
.env.docker          ← Your credentials (NEVER commit to git!)
├─ DB_USER          (PostgreSQL username)
├─ DB_PASSWORD      (PostgreSQL password)
├─ DB_NAME          (Database name)
├─ BINANCE_API_KEY  (API credentials)
└─ BINANCE_API_SECRET
```

#### 2. Docker Compose Now Uses These Variables
```yaml
environment:
  POSTGRES_USER: ${DB_USER}           # Reads from .env.docker
  POSTGRES_PASSWORD: ${DB_PASSWORD}
  POSTGRES_DB: ${DB_NAME}
  DATABASE_URL: postgresql://...      # Automatically constructed
```

#### 3. Git Won't Expose Your Secrets
```
.gitignore includes:
├─ .env
├─ .env.docker       ← Your credentials are safe!
├─ .env.production
└─ .env.*.local
```

---

## 🔐 How to Use (Step by Step)

### Step 1: Change Credentials in `.env.docker`

Edit `/home/preda/trading_dashboard/.env.docker`:

```bash
# Open and edit
nano /home/preda/trading_dashboard/.env.docker
```

Change these values to something secure:

```env
# CHANGE THESE!
DB_USER=investhor_trader              # Change this
DB_PASSWORD=YourSecurePasswordHere123! # VERY IMPORTANT - Change this!
DB_NAME=trading_dashboard

DEBUG=true                             # Set to false in production
BINANCE_API_KEY=your_binance_key_here  # Add your key
BINANCE_API_SECRET=your_binance_secret # Add your secret
```

**Tips for secure passwords:**
- Use mix of uppercase, lowercase, numbers, special chars
- At least 16 characters long
- Example: `Tr@d1ng_V1k1ng_2024!SecurePass`
- Never use real passwords from other services

### Step 2: Launch Docker with Credentials

```bash
# Go to project
cd /home/preda/trading_dashboard

# Docker will automatically read .env.docker
docker-compose up -d
```

Docker automatically finds `.env.docker` and uses those values! ✅

### Step 3: Verify Credentials Work

```bash
# Test database connection
docker-compose exec investhor_db psql -U investhor_trader -d trading_dashboard -c "\dt"

# You'll be prompted for password (use the one from .env.docker)
# If it works, you'll see the tables!
```

---

## 🚨 Important Security Rules

### ❌ NEVER DO THIS:
```
❌ Commit .env.docker to git
❌ Hardcode passwords in docker-compose.yml
❌ Use simple passwords like "password" or "123456"
❌ Share .env.docker file with others
❌ Commit API keys to git
```

### ✅ DO THIS INSTEAD:
```
✅ Keep .env.docker in .gitignore (already done!)
✅ Use environment variables
✅ Use strong, unique passwords
✅ Share credentials securely (1Password, Vault, etc.)
✅ Rotate credentials periodically
```

---

## 📋 Environment Variables Reference

### Database Variables
```env
DB_USER=investhor_trader              # PostgreSQL user
DB_PASSWORD=YourSecurePassword123!    # PostgreSQL password
DB_NAME=trading_dashboard             # Database name
```

These are used for:
- Creating PostgreSQL user
- Setting up database
- Backend connection string

### Backend Variables
```env
DEBUG=true                             # Development mode (false for production)
BINANCE_API_KEY=your_key              # Binance trading API key
BINANCE_API_SECRET=your_secret        # Binance trading API secret
```

### Derived Variables
These are automatically built from above:
```
DATABASE_URL = postgresql://${DB_USER}:${DB_PASSWORD}@investhor_db:5432/${DB_NAME}
```

---

## 🔒 Different Environments

### Development (What You Have Now)
```
.env.docker
├─ Local test credentials
├─ DEBUG=true
└─ Safe to use anything
```

### Production (When You Deploy)
```
.env.production
├─ Real, strong credentials
├─ DEBUG=false
├─ Real API keys
└─ NEVER committed to git
```

**To use production credentials:**
```bash
# Copy template
cp .env.docker .env.production

# Edit with real credentials
nano .env.production

# Tell Docker to use it
docker-compose --env-file .env.production up -d
```

---

## 🛡️ Password Generator

Need a secure password? Use this:

```bash
# Generate random 32-character password
openssl rand -base64 32

# Example output:
# abc123XYZ+/==abc123XYZ+/==abc123XYZ+/==
```

Then use it in `.env.docker`:
```env
DB_PASSWORD=abc123XYZ+/==abc123XYZ+/==abc123XYZ+/==
```

---

## 🔄 Changing Credentials Later

If you need to change the database password later:

### Option 1: Easy Way (Start Fresh)
```bash
# Stop everything
docker-compose down -v

# Edit .env.docker with new password
nano .env.docker

# Start fresh
docker-compose up -d
```

### Option 2: Hard Way (Keep Data)
```bash
# Connect to database
docker-compose exec investhor_db psql -U investhor_trader -d trading_dashboard

# In psql shell:
ALTER USER investhor_trader WITH PASSWORD 'new_secure_password';
\q

# Update .env.docker
nano .env.docker

# Restart backend
docker-compose restart investhor_backend
```

---

## 🔍 Checking Your Setup

### Is .env.docker being used?
```bash
# Check docker-compose reads from .env.docker
docker-compose config | grep POSTGRES_USER

# Should show: POSTGRES_USER: investhor_trader (from .env.docker)
```

### Is .env.docker in .gitignore?
```bash
# Check if it's ignored
git status

# Should NOT show .env.docker in untracked files
```

### What credentials are the containers using?
```bash
# Check environment variables in running container
docker-compose exec investhor_backend env | grep DATABASE_URL

# Should show: DATABASE_URL=postgresql://investhor_trader:***@...
```

---

## 🌍 Caddy + Credentials

When deploying with Caddy, you'll need:

### Backend .env File
```env
DATABASE_URL=postgresql://investhor_trader:SecurePassword@investhor_db:5432/trading_dashboard
DEBUG=false
PRODUCTION_DOMAIN=https://yourdomain.com
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

### Docker Compose .env File (.env.docker)
```env
DB_USER=investhor_trader
DB_PASSWORD=SecurePassword
DB_NAME=trading_dashboard
DEBUG=false
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

Both should have **matching credentials**!

---

## 📝 Checklist Before Going Live

- [ ] Changed DB_PASSWORD in .env.docker to something secure
- [ ] Verified .env.docker is in .gitignore
- [ ] Tested connection: `docker-compose exec investhor_db psql -U ...`
- [ ] Checked git status - NO .env.docker showing as modified
- [ ] Added Binance API keys (if using real trading)
- [ ] Set DEBUG=false for production
- [ ] Used strong, unique passwords (16+ chars)
- [ ] Never committed credentials to git
- [ ] Documented credentials securely (1Password, Vault, etc.)

---

## 🚨 If You Accidentally Committed Credentials

**Don't panic! Do this immediately:**

```bash
# Remove from git history
git rm --cached .env.docker
git commit -m "Remove sensitive credentials"

# Force push (be careful!)
git push --force-with-lease origin main

# CHANGE THE PASSWORDS IMMEDIATELY
# Edit .env.docker with new values
docker-compose down -v
docker-compose up -d
```

Then:
1. **Rotate all API keys** (especially Binance)
2. **Change database password**
3. Never use those credentials again!

---

## 📚 References

- [Docker Env Variables Docs](https://docs.docker.com/compose/environment-variables/)
- [PostgreSQL Security](https://www.postgresql.org/docs/)
- [Best Practices for Secrets](https://12factor.net/config)

---

## 🛡️ Summary

✅ You now have:
- Secure credential management with `.env.docker`
- Git protection (credentials never committed)
- Easy credential rotation
- Environment variable support
- Development/Production separation

⚠️ Remember:
- Keep `.env.docker` in `.gitignore`
- Never hardcode passwords
- Use strong, unique passwords
- Rotate credentials periodically

---

**Your InvesThor fortress is now secure! 🛡️⚔️**
