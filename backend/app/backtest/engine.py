"""Event-driven long/flat backtester.

Pure function (no DB/network). Walks bars, asks the strategy for signals, and
simulates a long-only account: a BUY deploys all cash into the asset, a SELL
flattens. Fees and slippage are flat basis points. Returns an equity curve and
summary metrics.
"""
import math
from statistics import mean, pstdev


def run(bars, strategy, *, initial_cash=10_000.0, fee_bps=10.0, slippage_bps=5.0) -> dict:
    cash = float(initial_cash)
    qty = 0.0
    entry_price = 0.0
    trades = []  # realized round-trips: {"pnl": float}
    equity_curve = []

    fee = fee_bps / 10_000.0
    slip = slippage_bps / 10_000.0

    for i, bar in enumerate(bars):
        close = bar["close"]
        sig = strategy.on_bar(i, bars)
        action = sig.action.upper() if sig else "HOLD"

        if action == "BUY" and qty == 0.0 and cash > 0:
            fill = close * (1 + slip)
            notional = cash
            fee_paid = notional * fee
            qty = (notional - fee_paid) / fill
            entry_price = fill
            cash = 0.0
        elif action == "SELL" and qty > 0.0:
            fill = close * (1 - slip)
            proceeds = qty * fill
            proceeds -= proceeds * fee
            pnl = proceeds - (qty * entry_price)
            trades.append({"pnl": pnl})
            cash = proceeds
            qty = 0.0
            entry_price = 0.0

        equity = cash + qty * close
        equity_curve.append({"ts": bar["ts"], "equity": equity})

    final_equity = equity_curve[-1]["equity"] if equity_curve else initial_cash
    metrics = _metrics(equity_curve, trades, initial_cash, final_equity, bars)
    return {"equity_curve": equity_curve, "metrics": metrics, "final_equity": final_equity}


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

    wins = [t for t in trades if t["pnl"] > 0]
    buy_hold = (bars[-1]["close"] / bars[0]["close"] - 1.0) if len(bars) >= 2 else 0.0

    return {
        "total_return": total_return,
        "buy_hold_return": buy_hold,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "num_trades": len(trades),
        "win_rate": (len(wins) / len(trades)) if trades else 0.0,
        "final_equity": final_equity,
    }
