# Multi-Ticker Selection Design

## Summary
Add a configurable ticker dropdown to the Dashboard that controls both the chart and Quick Stats panel. Users can select from default pairs and add custom ones.

## Architecture
Single `selectedSymbol` reactive ref in Dashboard.vue drives both chart and stats. When changed:
- ChartComponent re-initializes via existing `watch` on `props.symbol`
- Stats panel unsubscribes from old ticker WS, subscribes to new one
- Quick Stats title updates to show current symbol

## UI
Chart header changes from hardcoded "Bitcoin Battle Chart" to a styled dropdown + timeframe buttons:
- `[▼ BTC/USDT]` | `[1H] [4H] [1D] [1W]`
- Dropdown matches dark purple theme
- Default pairs: BTC, ETH, BNB, SOL, XRP (all vs USDT)

## Configurable List
- Default pairs as const array
- "Add pair" input lets users type Binance symbols (e.g. DOTUSDT)
- Custom pairs persist in localStorage
- Remove button (X) on custom-added pairs

## Files Changed
- `Dashboard.vue` — add selectedSymbol ref, dropdown UI, localStorage, update stats subscription
- `ChartComponent.vue` — no changes needed (already accepts symbol prop + watches)

## Data Flow
```
selectedSymbol changes →
  ├─ ChartComponent receives new :symbol prop → cleanup + reinit
  ├─ Dashboard unsubscribes old ticker WS → subscribes new
  └─ Quick Stats title updates
```
