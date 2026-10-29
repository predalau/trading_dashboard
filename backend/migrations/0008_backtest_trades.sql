-- Store per-backtest trade events (entry/exit ts + price + pnl) so the UI can
-- plot entries and exits on a price chart.
ALTER TABLE backtests ADD COLUMN IF NOT EXISTS trades JSONB;
