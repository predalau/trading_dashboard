"""Event-driven long/flat backtester.

Pure function (no DB/network). Walks bars, asks the strategy for signals, and
simulates a long-only account: a BUY deploys all cash into the asset, a SELL
flattens. Fees and slippage are flat basis points. Returns an equity curve and
summary metrics.
"""
import math
from statistics import mean, pstdev


def run(bars, strategy, *, initial_cash=10_000.0, fee_bps=10.0, slippage_bps=5.0,
        bias=None, entry_threshold=-1.0, exit_threshold=None) -> dict:
    """Event-driven long/flat backtest.

    Optional multi-timeframe trend bias: `bias` is a per-bar score in -1..+1.
    Entries (BUY) are only taken when bias[i] >= entry_threshold. If
    exit_threshold is set, an open position is force-closed when bias[i] <=
    exit_threshold (regardless of the strategy's own signal).
    """
    cash = float(initial_cash)
    qty = 0.0
    entry_price = 0.0
    trades = []  # round-trips: {entry_ts, entry_price, exit_ts, exit_price, pnl}
    open_trade = None
    equity_curve = []

    fee = fee_bps / 10_000.0
    slip = slippage_bps / 10_000.0

    def _bias(i):
        return bias[i] if (bias is not None and i < len(bias)) else None

    for i, bar in enumerate(bars):
        close = bar["close"]
        sig = strategy.on_bar(i, bars)
        action = sig.action.upper() if sig else "HOLD"

        # Multi-timeframe gate: block entries that fight the higher-TF trend
        b = _bias(i)
        if action == "BUY" and b is not None and b < entry_threshold:
            action = "HOLD"
        # Force-exit when the higher-TF trend flips hard against an open long
        if (qty > 0.0 and exit_threshold is not None and b is not None
                and b <= exit_threshold):
            action = "SELL"

        if action == "BUY" and qty == 0.0 and cash > 0:
            fill = close * (1 + slip)
            notional = cash
            fee_paid = notional * fee
            qty = (notional - fee_paid) / fill
            entry_price = fill
            cash = 0.0
            open_trade = {"entry_ts": bar["ts"], "entry_price": fill,
                          "exit_ts": None, "exit_price": None, "pnl": None}
            trades.append(open_trade)
        elif action == "SELL" and qty > 0.0:
            fill = close * (1 - slip)
            proceeds = qty * fill
            proceeds -= proceeds * fee
            pnl = proceeds - (qty * entry_price)
            if open_trade is not None:
                open_trade["exit_ts"] = bar["ts"]
                open_trade["exit_price"] = fill
                open_trade["pnl"] = pnl
            open_trade = None
            cash = proceeds
            qty = 0.0
            entry_price = 0.0

        equity = cash + qty * close
        equity_curve.append({"ts": bar["ts"], "equity": equity})

    final_equity = equity_curve[-1]["equity"] if equity_curve else initial_cash
    metrics = _metrics(equity_curve, trades, initial_cash, final_equity, bars)
    return {"equity_curve": equity_curve, "trades": trades,
            "metrics": metrics, "final_equity": final_equity}


def _metrics(equity_curve, trades, initial_cash, final_equity, bars) -> dict:
    total_return = (final_equity / initial_cash - 1.0) if initial_cash else 0.0

    # Max drawdown (fraction, <= 0).
    peak = -math.inf
    max_dd = 0.0
    for point in equity_curve:
        eq = point["equity"]
        peak = max(peak, eq)
        if peak > 0:
            max_dd = min(max_dd, eq / peak - 1.0)

    # Per-bar simple returns -> rough Sharpe (not annualized).
    eqs = [p["equity"] for p in equity_curve]
    rets = [eqs[i] / eqs[i - 1] - 1.0 for i in range(1, len(eqs)) if eqs[i - 1] > 0]
    sharpe = 0.0
    if len(rets) > 1:
        sd = pstdev(rets)
        if sd > 0:
            sharpe = (mean(rets) / sd) * math.sqrt(len(rets))

    wins = [t for t in trades if (t.get("pnl") or 0) > 0]
    closed = [t for t in trades if t.get("pnl") is not None]
    buy_hold = (bars[-1]["close"] / bars[0]["close"] - 1.0) if len(bars) >= 2 else 0.0

    return {
        "total_return": total_return,
        "buy_hold_return": buy_hold,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "num_trades": len(closed),
        "win_rate": (len(wins) / len(closed)) if closed else 0.0,
        "final_equity": final_equity,
    }
