# Trading Dashboard - Development Setup Guide

## Initial Setup Steps

### 1. Clone the Repository

```bash
git clone git@github.com:predalau/trading_dashboard.git
cd trading_dashboard
```

### 2. Configure Environment Variables

#### Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
```

Example `.env` for local development:
```env
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_dashboard
DEBUG=true
BINANCE_API_KEY=your_binance_key_here
BINANCE_API_SECRET=your_binance_secret_here
```

#### Frontend
```bash
cd frontend
cp .env.example .env.local
# The defaults work for local development
```

### 3. Database Setup

#### Option A: Using Docker
```bash
docker-compose up -d postgres
# Wait for postgres to be healthy (check with: docker ps)
```

#### Option B: Local PostgreSQL
```bash
# Create database
createdb trading_dashboard

# Create user (if needed)
psql -U postgres
CREATE USER trading_user WITH PASSWORD 'trading_password';
GRANT ALL PRIVILEGES ON DATABASE trading_dashboard TO trading_user;
\q

# Apply schema
psql -U trading_user -d trading_dashboard -f database/schema.sql
```

### 4. Backend Installation & Running

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload
```

Server runs on: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 5. Frontend Installation & Running

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: `http://localhost:5173`

### 6. Verify Everything Works

Visit these URLs:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Available Commands

### Backend
```bash
# Run server with auto-reload
python -m uvicorn app.main:app --reload

# Run tests
pytest tests/

# Run with specific host/port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images
docker-compose up -d --build
```

## Troubleshooting

### "Connection refused" to PostgreSQL
- Ensure PostgreSQL is running: `psql -U postgres` (should connect)
- Check DATABASE_URL is correct in .env
- Verify database exists: `psql -l`

### Port 8000 already in use
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Port 5173 already in use
```bash
# Kill process on port 5173
lsof -i :5173 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Module not found errors in Backend
```bash
# Ensure venv is activated
which python  # Should show path inside venv/
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### npm ERR in Frontend
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS errors
- Frontend is trying to call backend at different origin
- Check that frontend URL is in CORS allowed_origins in backend/app/main.py
- Default: `http://localhost:5173` should work

## Development Workflow

1. **Backend Changes**:
   - Edit files in `backend/app/`
   - Server auto-reloads with `--reload` flag
   - Test with http://localhost:8000/docs

2. **Frontend Changes**:
   - Edit files in `frontend/src/`
   - Browser auto-refreshes (HMR)
   - Check browser console for errors

3. **Database Changes**:
   - Update `database/schema.sql`
   - Restart PostgreSQL container or reload database
   - Consider creating migrations for production

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: description of changes"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## Adding New Dependencies

### Backend
```bash
pip install package-name
pip freeze > requirements.txt  # Update requirements
```

### Frontend
```bash
npm install package-name
npm install --save-dev package-name  # For dev dependencies
```

## API Integration Testing

### Using curl
```bash
# Create account
curl -X POST http://localhost:8000/api/v1/paper-trading/accounts \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "account_name": "Test", "initial_balance": 10000}'

# Get price
curl http://localhost:8000/api/v1/market/price/BTCUSDT?exchange=BINANCE
```

### Using Postman/Insomnia
- Import API from http://localhost:8000/openapi.json
- Or use http://localhost:8000/docs interface directly

## Database Management

### View tables
```bash
psql -U trading_user -d trading_dashboard -c "\dt"
```

### View trades
```bash
psql -U trading_user -d trading_dashboard -c "SELECT * FROM trades;"
```

### Reset database (development only)
```bash
dropdb -U trading_user trading_dashboard
createdb -U trading_user trading_dashboard
psql -U trading_user -d trading_dashboard -f database/schema.sql
```

## Performance Optimization Notes

- Frontend: CSS animations are pure CSS (no JavaScript overhead)
- Backend: Using async/await with FastAPI for concurrent handling
- Database: Indexes created on frequently queried columns
- Charts: TradingView Lightweight Charts is optimized for large datasets

## Next Steps

1. Start the development servers (steps 4-5)
2. Open frontend at http://localhost:5173
3. Explore the dashboard interface
4. Create a paper trading account
5. Place trades and monitor portfolio
6. Check API docs at http://localhost:8000/docs

---

**Happy Coding! 🚀**
