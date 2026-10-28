from strategies.base import Strategy, Signal

class Momentum(Strategy):
    params = {"lookback": 12}
    def on_bar(self, i, bars):
        n = int(self.params["lookback"])
        if i < n:
            return None
        if bars[i]["close"] > bars[i - n]["close"]:
            return Signal("BUY")
        return Signal("SELL")
