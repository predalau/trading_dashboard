"""Bollinger Band mean-reversion: buy below the lower band, sell above the upper."""
from strategies.base import Signal, Strategy
from strategies.indicators import bollinger


class Bollinger(Strategy):
    name = "Bollinger Reversion"
    description = "Buy when price closes below the lower band; sell when it closes above the upper band."
    params = {"period": 20, "num_std": 2.0}
    param_spec = [
        {"name": "period", "label": "period", "type": "int", "min": 5, "max": 100, "step": 1},
        {"name": "num_std", "label": "std-dev mult", "type": "float", "min": 0.5, "max": 4.0, "step": 0.1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        _, upper, lower = bollinger(closes, n, float(self.params["num_std"]))
        c = closes[-1]
        if c < lower:
            return Signal("BUY")
        if c > upper:
            return Signal("SELL")
        return None
