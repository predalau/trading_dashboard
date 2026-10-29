"""EMA crossover: long when the fast EMA crosses above the slow EMA."""
from strategies.base import Signal, Strategy
from strategies.indicators import ema


class EmaCross(Strategy):
    name = "EMA Crossover"
    description = "Long when fast EMA crosses above slow EMA; exit on the reverse cross."
    params = {"fast": 12, "slow": 26}
    param_spec = [
        {"name": "fast", "label": "fast EMA", "type": "int", "min": 2, "max": 100, "step": 1},
        {"name": "slow", "label": "slow EMA", "type": "int", "min": 5, "max": 300, "step": 1},
    ]

    def on_bar(self, i, bars):
        fast = int(self.params["fast"])
        slow = int(self.params["slow"])
        if i < slow:
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        f_now, s_now = ema(closes, fast), ema(closes, slow)
        f_prev, s_prev = ema(closes[:-1], fast), ema(closes[:-1], slow)
        if f_prev <= s_prev and f_now > s_now:
            return Signal("BUY")
        if f_prev >= s_prev and f_now < s_now:
            return Signal("SELL")
        return None
