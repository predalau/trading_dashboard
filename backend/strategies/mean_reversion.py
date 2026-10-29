"""Z-score mean-reversion around a moving average."""
from strategies.base import Signal, Strategy
from strategies.indicators import stddev


class MeanReversion(Strategy):
    name = "Z-Score Reversion"
    description = "Buy when price is >threshold std-devs below its mean; sell when >threshold above."
    params = {"period": 20, "threshold": 1.5}
    param_spec = [
        {"name": "period", "label": "lookback", "type": "int", "min": 5, "max": 100, "step": 1},
        {"name": "threshold", "label": "z threshold", "type": "float", "min": 0.5, "max": 4.0, "step": 0.1},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        window = [b["close"] for b in bars[i - n + 1:i + 1]]
        m = sum(window) / n
        sd = stddev(window)
        if sd == 0:
            return None
        z = (bars[i]["close"] - m) / sd
        t = float(self.params["threshold"])
        if z < -t:
            return Signal("BUY")
        if z > t:
            return Signal("SELL")
        return None
