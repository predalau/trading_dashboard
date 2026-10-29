"""Trend filter: long while price is above its SMA, flat below."""
from strategies.base import Signal, Strategy
from strategies.indicators import sma


class SmaTrend(Strategy):
    name = "Price vs SMA"
    description = "Long while price is above its simple moving average; flat below it."
    params = {"period": 50}
    param_spec = [
        {"name": "period", "label": "SMA period", "type": "int", "min": 5, "max": 300, "step": 1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        return Signal("BUY") if closes[-1] > sma(closes, n) else Signal("SELL")
