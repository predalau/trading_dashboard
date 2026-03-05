# Trade Entry/SL/TP Visualization Design

## Summary
Add trade position visualization on the chart using lightweight-charts' `createPriceLine()` and `setMarkers()`. Users can create trades with entry, stop loss, and take profit levels that appear as colored horizontal lines on the chart.

## Library Decision
Stay with lightweight-charts (no library change needed). It supports:
- `series.createPriceLine()` for horizontal lines at specific prices
- `series.setMarkers()` for trade entry/exit point markers
- Click coordinate translation via `series.coordinateToPrice()`

## Database Changes
Add two columns to `trades` table:
- `stop_loss DECIMAL(20, 8)` - nullable
- `take_profit DECIMAL(20, 8)` - nullable

## Backend API
New endpoints under `/api/v1/trades/`:
- `GET /trades/?symbol=BTCUSDT&open=true` - open trades for chart rendering
- `POST /trades/` - create trade with entry, SL, TP
- `PATCH /trades/{id}` - update SL/TP
- `DELETE /trades/{id}` - close/remove trade

## Chart Visualization
- Entry line: purple dashed, label "Entry $X"
- Stop Loss line: red dashed, label "SL $X"
- Take Profit line: green dashed, label "TP $X"
- Entry marker: triangle on entry candle

## Trade Panel UI
Collapsible panel below chart:
- New Trade form (side, entry, SL, TP, quantity)
- Active trades list with edit/close
- Click-to-set mode: click chart to set Entry → SL → TP sequentially

## Data Flow
```
Create: User form/click → POST /trades/ → DB → price lines on chart
Update: Edit SL/TP → PATCH /trades/{id} → DB → update lines
Delete: Close trade → DELETE /trades/{id} → DB → remove lines
Load:   Symbol change → GET /trades/?symbol=X → render all open trade lines
```

## Files Changed
- `database/schema.sql` - add stop_loss, take_profit columns
- `backend/app/models.py` - add fields to Trade model
- `backend/app/api/trades.py` - new CRUD endpoints
- `backend/app/services/trade_service.py` - trade management logic
- `backend/app/main.py` - register router
- `frontend/src/components/ChartComponent.vue` - price lines, markers, click handler
- `frontend/src/pages/Dashboard.vue` - trade panel UI
