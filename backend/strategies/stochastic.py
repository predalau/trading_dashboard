"""Stochastic oscillator %K: buy oversold, sell overbought."""
from strategies.base import Signal, Strategy


class Stochastic(Strategy):
    name = "Stochastic Oscillator"
    description = "Buy when %K drops below oversold; sell when it rises above overbought."
    params = {"period": 14, "oversold": 20, "overbought": 80}
    param_spec = [
        {"name": "period", "label": "%K period", "type": "int", "min": 3, "max": 50, "step": 1},
        {"name": "oversold", "label": "oversold", "type": "int", "min": 5, "max": 40, "step": 1},
        {"name": "overbought", "label": "overbought", "type": "int", "min": 60, "max": 95, "step": 1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        window = bars[i - n + 1:i + 1]
        hh = max(b["high"] for b in window)
        ll = min(b["low"] for b in window)
        if hh == ll:
            return None
        k = (bars[i]["close"] - ll) / (hh - ll) * 100.0
        if k < self.params["oversold"]:
            return Signal("BUY")
        if k > self.params["overbought"]:
            return Signal("SELL")
        return None
