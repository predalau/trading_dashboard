"""SMA crossover: go long when fast SMA crosses above slow SMA, exit on the
reverse cross. Reference strategy / template for MCP-authored strategies.
"""
from strategies.base import Signal, Strategy


class SmaCross(Strategy):
    params = {"fast": 10, "slow": 30}

    def on_bar(self, i, bars):
        fast = int(self.params["fast"])
        slow = int(self.params["slow"])
        if i < slow:  # need a full slow window plus one prior bar
            return None
        closes = [b["close"] for b in bars[: i + 1]]
        fast_now = sum(closes[-fast:]) / fast
        slow_now = sum(closes[-slow:]) / slow
        fast_prev = sum(closes[-fast - 1:-1]) / fast
        slow_prev = sum(closes[-slow - 1:-1]) / slow
        if fast_prev <= slow_prev and fast_now > slow_now:
            return Signal("BUY")
        if fast_prev >= slow_prev and fast_now < slow_now:
            return Signal("SELL")
        return None
