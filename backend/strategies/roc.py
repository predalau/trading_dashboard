"""Rate-of-change momentum: long while N-bar return exceeds a threshold."""
from strategies.base import Signal, Strategy


class Roc(Strategy):
    name = "Rate of Change"
    description = "Long while the N-bar percent change is above the threshold; flat otherwise."
    params = {"period": 12, "threshold": 0.0}
    param_spec = [
        {"name": "period", "label": "lookback", "type": "int", "min": 2, "max": 100, "step": 1},
        {"name": "threshold", "label": "ROC threshold %", "type": "float", "min": -10.0, "max": 10.0, "step": 0.5},
    ]

    def on_bar(self, i, bars):
        n = int(self.params["period"])
        if i < n:
            return None
        prev = bars[i - n]["close"]
        if prev == 0:
            return None
        roc = (bars[i]["close"] / prev - 1.0) * 100.0
        return Signal("BUY") if roc > float(self.params["threshold"]) else Signal("SELL")
