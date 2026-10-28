# InvesThor

A full-stack trading dashboard for managing assets and backtesting strategies: paper trading, live Binance market data, and both a web UI and a REST API.

The UI uses the **Terminal Ice** theme: a dark, monospace, terminal-style interface (near-black ground, `#202d3d` surfaces, cyan accent, no green).

## Features

- **Paper trading**: place LONG/SHORT trades with stop loss and take profit, auto-closed when either is hit
- **Live charts**: TradingView Lightweight Charts fed by Binance REST + WebSocket, with entry/SL/TP lines and click-to-set prices
- **Live ticker and `sys.log`**: header ticker strip and an event log of connections, fills, SL/TP hits and API errors
- **Positions and history**: `ps --positions` table with live P&L and R, `cat history.log` of closed trades
- **Profile stats**: equity, total P&L, win rate and average realized R
- **Exchanges**: Binance (live), Solana and more planned
- **REST API**: programmatic access for algorithmic strategies
- **PostgreSQL** storage for accounts and trades

## Tech Stack

### Frontend
- **Framework**: Vue 3
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + CSS design tokens (Terminal Ice theme), pure CSS animations
- **Font**: JetBrains Mono (self-hosted via `@fontsource/jetbrains-mono`)
- **Charts**: TradingView Lightweight Charts
- **State Management**: Pinia
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Integrations**:
  - Binance REST API
  - Solana RPC (planned)
- **Package Manager**: pip with requirements.txt

### DevOps
- **Containerization**: Docker & Docker Compose
- **Development**: Hot-reload for both frontend and backend

## Project Structure

```
trading-dashboard/
├── frontend/                 # Vue 3 + Vite application
│   ├── src/
│   │   ├── components/      # ChartComponent + term/ UI building blocks
│   │   ├── pages/           # Home, Dashboard, Trades, Profile
│   │   ├── stores/          # Pinia stores (trading, log)
│   │   ├── services/        # Binance WebSocket client
│   │   ├── api/             # API client utilities
│   │   ├── App.vue          # Root component
│   │   ├── main.js          # Entry point
│   │   └── style.css        # Design tokens and shared .t-* styles
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── paper_trading.py
│   │   │   ├── market_data.py
│   │   │   └── user.py
│   │   ├── services/         # Business logic
│   │   │   ├── trading_service.py
│   │   │   └── market_service.py
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── database.py       # Database configuration
│   │   └── main.py           # FastAPI app
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── database/
│   └── schema.sql           # Database schema
│
├── docker-compose.yml       # Docker Compose configuration
├── .gitignore
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose (easiest method)
- OR:
  - Python 3.11+
  - Node.js 20+
  - PostgreSQL 16+

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone git@github.com:predalau/trading_dashboard.git
cd trading_dashboard

# Start all services
docker-compose up -d

# Frontend will be available at: http://localhost:5173
# Backend API at: http://localhost:8000
# API documentation at: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL
# (Make sure PostgreSQL is running and create the database)
createdb trading_dashboard

# Run migrations and start server
python -m uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## API Documentation

### Endpoints

#### Paper Trading
- `POST /api/v1/paper-trading/accounts` - Create paper trading account
- `GET /api/v1/paper-trading/accounts/{account_id}` - Get account details
- `POST /api/v1/paper-trading/trades/{account_id}` - Create new trade
- `GET /api/v1/paper-trading/trades/{account_id}` - Get account trades
- `PUT /api/v1/paper-trading/trades/{trade_id}` - Close a trade
- `GET /api/v1/paper-trading/portfolio/{account_id}` - Get portfolio summary

#### Trades (used by the web UI)
- `GET /api/v1/trades/?symbol=&open=` - List trades, filter by symbol and open/closed
- `POST /api/v1/trades/` - Create a trade
- `PATCH /api/v1/trades/{trade_id}` - Update SL, TP or notes
- `DELETE /api/v1/trades/{trade_id}` - Close a trade (optional `exit_price` body)

#### Market Data
- `GET /api/v1/market/price/{symbol}` - Get current price
- `GET /api/v1/market/klines/{symbol}` - Get candlestick data
- `GET /api/v1/market/24h/{symbol}` - Get 24h statistics
- `GET /api/v1/market/symbols` - List supported symbols

#### User Management
- `POST /api/v1/user/register` - Register new user
- `GET /api/v1/user/{user_id}` - Get user details

Full interactive API documentation available at `http://localhost:8000/docs`

## Example: Create a Paper Trading Account and Trade

```bash
# Create account
curl -X POST http://localhost:8000/api/v1/paper-trading/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "account_name": "My Trading Account",
    "initial_balance": 10000
  }'

# Create a BUY trade
curl -X POST http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "exchange": "BINANCE",
    "trade_type": "BUY",
    "entry_price": 43000,
    "quantity": 0.5,
    "notes": "Long position on Bitcoin"
  }'

# Close the trade
curl -X PUT http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{
    "exit_price": 44000,
    "notes": "Taking profit"
  }'
```

## Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/trading_dashboard
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
DEBUG=true
```

## Development

### Frontend Development
- Hot Module Replacement (HMR) enabled with Vite
- Component-based architecture with Vue 3 Composition API
- State management with Pinia stores

### Backend Development
- Auto-reload with `--reload` flag
- Interactive API docs with Swagger UI at `/docs`
- Alternative API docs with ReDoc at `/redoc`

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Deployment

### Docker Production Build

```bash
docker-compose -f docker-compose.yml up -d
```

### Environment Variables for Production

Set appropriate environment variables:
- `DEBUG=false`
- `DATABASE_URL` pointing to production PostgreSQL
- `BINANCE_API_KEY` and `BINANCE_API_SECRET`
- CORS origins adjusted for your domain

## Roadmap

- [ ] User authentication (JWT)
- [x] Stop loss and take profit (auto-closed client-side)
- [ ] Advanced order types (OCO, trailing stop)
- [ ] More exchange integrations (Solana, Kraken, etc.)
- [x] Real-time prices via Binance WebSocket
- [x] Terminal Ice UI redesign
- [ ] Strategy backtesting engine
- [ ] Advanced analytics and reporting
- [ ] Mobile app

## Performance Considerations

- **Charts**: TradingView Lightweight Charts is optimized for rendering large datasets
- **Database**: Indexes on frequently queried columns (symbol, timestamp, account_id)
- **API**: Async/await with FastAPI for concurrent request handling
- **Frontend**: Lazy loading of components, optimized CSS animations (pure CSS, no JS overhead)

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -an | grep 8000

# Find process using port 5173
lsof -i :5173
```

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists and user has permissions

### CORS Errors
- Check frontend URL is in CORS allowed origins in `app/main.py`
- Default local URLs: `http://localhost:5173`, `http://localhost:3000`

## Contributing

1. Create a feature branch
2. Commit changes
3. Push to GitHub
4. Create a Pull Request

## License

MIT License

## Support

For issues, questions, or suggestions:
1. Check existing issues on GitHub
2. Create a new issue with detailed information
3. Include error logs and reproduction steps

---

**Happy trading.**
