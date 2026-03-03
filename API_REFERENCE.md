# Trading Dashboard API Reference

Base URL: `http://localhost:8000/api/v1`

## Authentication
Currently no authentication required for development. Add JWT/OAuth for production.

---

## Paper Trading Endpoints

### Create Paper Trading Account
```http
POST /paper-trading/accounts
Content-Type: application/json

{
  "user_id": 1,
  "account_name": "My Trading Account",
  "initial_balance": 10000
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "account_name": "My Trading Account",
  "initial_balance": 10000,
  "current_balance": 10000,
  "available_balance": 10000,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Get Account Details
```http
GET /paper-trading/accounts/{account_id}
```

**Response:** Account object (see Create response above)

---

### Create Trade
```http
POST /paper-trading/trades/{account_id}
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "trade_type": "BUY",
  "entry_price": 43000,
  "quantity": 0.5,
  "notes": "Long position"
}
```

**Response:**
```json
{
  "id": 1,
  "account_id": 1,
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "trade_type": "BUY",
  "entry_price": 43000,
  "quantity": 0.5,
  "entry_time": "2024-01-15T10:35:00Z",
  "exit_price": null,
  "exit_time": null,
  "profit_loss": null,
  "profit_loss_percentage": null,
  "is_open": true,
  "notes": "Long position"
}
```

**Error Responses:**
- `400 Bad Request`: Insufficient balance
- `404 Not Found`: Account not found

---

### Get All Trades for Account
```http
GET /paper-trading/trades/{account_id}
GET /paper-trading/trades/{account_id}?is_open=true
GET /paper-trading/trades/{account_id}?is_open=false
```

**Query Parameters:**
- `is_open` (optional): Filter by open/closed trades

**Response:**
```json
[
  {
    "id": 1,
    "account_id": 1,
    "symbol": "BTCUSDT",
    "exchange": "BINANCE",
    "trade_type": "BUY",
    "entry_price": 43000,
    "quantity": 0.5,
    "entry_time": "2024-01-15T10:35:00Z",
    "exit_price": null,
    "exit_time": null,
    "profit_loss": null,
    "profit_loss_percentage": null,
    "is_open": true,
    "notes": "Long position"
  }
]
```

---

### Close Trade
```http
PUT /paper-trading/trades/{trade_id}
Content-Type: application/json

{
  "exit_price": 44500,
  "notes": "Closed with profit"
}
```

**Response:**
```json
{
  "id": 1,
  "account_id": 1,
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "trade_type": "BUY",
  "entry_price": 43000,
  "quantity": 0.5,
  "entry_time": "2024-01-15T10:35:00Z",
  "exit_price": 44500,
  "exit_time": "2024-01-15T11:00:00Z",
  "profit_loss": 750,
  "profit_loss_percentage": 3.49,
  "is_open": false,
  "notes": "Closed with profit"
}
```

---

### Get Portfolio Summary
```http
GET /paper-trading/portfolio/{account_id}
```

**Response:**
```json
{
  "account": {
    "id": 1,
    "account_name": "My Trading Account",
    "initial_balance": 10000,
    "current_balance": 10750,
    "available_balance": 10750,
    "is_active": true
  },
  "open_trades_count": 2,
  "closed_trades_count": 1,
  "total_realized_profit_loss": 750,
  "cash_balance": 10750
}
```

---

## Market Data Endpoints

### Get Current Price
```http
GET /market/price/{symbol}
GET /market/price/BTCUSDT?exchange=BINANCE
```

**Query Parameters:**
- `exchange` (optional, default: BINANCE): Exchange to fetch from

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "price": 43250.50,
  "volume_24h": 2500000000,
  "high_24h": 44000,
  "low_24h": 42100,
  "change_24h_percent": 2.5
}
```

---

### Get Candlestick Data (Klines)
```http
GET /market/klines/BTCUSDT?interval=1h&limit=100&exchange=BINANCE
```

**Query Parameters:**
- `interval` (default: 1h): 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M
- `limit` (default: 100, max: 1000): Number of candles
- `exchange` (default: BINANCE): Exchange

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "exchange": "BINANCE",
  "klines": [
    {
      "time": 1705318800,
      "open": 43000,
      "high": 43500,
      "low": 42900,
      "close": 43200,
      "volume": 125000000
    }
  ]
}
```

---

### Get 24h Statistics
```http
GET /market/24h/BTCUSDT
GET /market/24h/BTCUSDT?exchange=BINANCE
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "price": 43250.50,
  "price_change": 1062.50,
  "price_change_percent": 2.51,
  "high": 44000,
  "low": 42100,
  "volume": 2500000000,
  "quote_asset_volume": 107500000000,
  "open_time": 1705232400000,
  "close_time": 1705318800000
}
```

---

### Get Supported Symbols
```http
GET /market/symbols?exchange=BINANCE
```

**Response:**
```json
{
  "exchange": "BINANCE",
  "symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "ADAUSDT",
    "DOGEUSDT"
  ]
}
```

---

## User Endpoints

### Register User
```http
POST /user/register
Content-Type: application/json

{
  "username": "trader123",
  "email": "trader@example.com"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "trader123",
  "email": "trader@example.com",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Username or email already exists

---

### Get User
```http
GET /user/{user_id}
```

**Response:**
```json
{
  "id": 1,
  "username": "trader123",
  "email": "trader@example.com",
  "created_at": "2024-01-15T10:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: User not found

---

## Health & System Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### API Root
```http
GET /api/v1
```

**Response:**
```json
{
  "message": "Trading Dashboard API",
  "version": "0.1.0",
  "endpoints": {
    "paper_trading": "/api/v1/paper-trading",
    "market_data": "/api/v1/market",
    "user": "/api/v1/user"
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes
- `200 OK`: Success
- `400 Bad Request`: Invalid input or insufficient funds
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Example Workflows

### Complete Trading Workflow

1. **Register User**
```bash
curl -X POST http://localhost:8000/api/v1/user/register \
  -H "Content-Type: application/json" \
  -d '{"username": "trader", "email": "trader@example.com"}'
```

2. **Create Account**
```bash
curl -X POST http://localhost:8000/api/v1/paper-trading/accounts \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "account_name": "Main", "initial_balance": 10000}'
```

3. **Get Price**
```bash
curl http://localhost:8000/api/v1/market/price/BTCUSDT?exchange=BINANCE
```

4. **Create Buy Trade**
```bash
curl -X POST http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "exchange": "BINANCE",
    "trade_type": "BUY",
    "entry_price": 43000,
    "quantity": 0.5,
    "notes": "Entry point"
  }'
```

5. **Get Portfolio**
```bash
curl http://localhost:8000/api/v1/paper-trading/portfolio/1
```

6. **Close Trade**
```bash
curl -X PUT http://localhost:8000/api/v1/paper-trading/trades/1 \
  -H "Content-Type: application/json" \
  -d '{"exit_price": 44000, "notes": "Exit"}'
```

---

## Rate Limiting

Currently no rate limiting. Add for production.

## WebSocket Support

Coming soon for real-time updates.

## Pagination

Coming soon for large result sets.

---

For interactive API testing, visit: http://localhost:8000/docs
