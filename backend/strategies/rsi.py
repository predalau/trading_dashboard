"""RSI mean-reversion: buy oversold, sell overbought."""
from strategies.base import Signal, Strategy
from strategies.indicators import rsi


class Rsi(Strategy):
    name = "RSI Reversion"
    description = "Buy when RSI falls below the oversold level; sell when it rises above overbought."
    params = {"period": 14, "oversold": 30, "overbought": 70}
    param_spec = [
        {"name": "period", "label": "RSI period", "type": "int", "min": 2, "max": 50, "step": 1},
        {"name": "oversold", "label": "oversold", "type": "int", "min": 5, "max": 45, "step": 1},
        {"name": "overbought", "label": "overbought", "type": "int", "min": 55, "max": 95, "step": 1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        r = rsi(closes, n)
        if r is None:
            return None
        if r < self.params["oversold"]:
            return Signal("BUY")
        if r > self.params["overbought"]:
            return Signal("SELL")
        return None
