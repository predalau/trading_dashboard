"""MACD crossover: long when the MACD line crosses above its signal line."""
from strategies.base import Signal, Strategy
from strategies.indicators import macd


class Macd(Strategy):
    name = "MACD Crossover"
    description = "Long when the MACD line crosses above its signal line; exit on the reverse."
    params = {"fast": 12, "slow": 26, "signal": 9}
    param_spec = [
        {"name": "fast", "label": "fast EMA", "type": "int", "min": 2, "max": 50, "step": 1},
        {"name": "slow", "label": "slow EMA", "type": "int", "min": 5, "max": 100, "step": 1},
        {"name": "signal", "label": "signal EMA", "type": "int", "min": 2, "max": 50, "step": 1},
    ]

    def on_bar(self, i, bars):
        fast = int(self.params["fast"])
        slow = int(self.params["slow"])
        signal = int(self.params["signal"])
        if i < slow + signal:
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        now = macd(closes, fast, slow, signal)
        prev = macd(closes[:-1], fast, slow, signal)
        if not now or not prev:
            return None
        m_now, s_now = now
        m_prev, s_prev = prev
        if m_prev <= s_prev and m_now > s_now:
            return Signal("BUY")
        if m_prev >= s_prev and m_now < s_now:
            return Signal("SELL")
        return None
