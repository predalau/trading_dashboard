"""Donchian channel breakout: buy on a new N-bar high, exit on a new N-bar low."""
from strategies.base import Signal, Strategy


class Donchian(Strategy):
    name = "Donchian Breakout"
    description = "Buy on a breakout above the prior N-bar high; exit on a break below the N-bar low."
    params = {"period": 20}
    param_spec = [
        {"name": "period", "label": "channel period", "type": "int", "min": 5, "max": 100, "step": 1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        prior = bars[i - n:i]  # exclude the current bar
        hh = max(b["high"] for b in prior)
        ll = min(b["low"] for b in prior)
        c = bars[i]["close"]
        if c > hh:
            return Signal("BUY")
        if c < ll:
            return Signal("SELL")
        return None
