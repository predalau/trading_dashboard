"""Strategy base interface for the backtester.

A strategy inspects bars up to index i and returns a Signal (or None = hold).
Bars are dicts: {ts, open, high, low, close, volume}. Strategies are pure
(no I/O); the backtester handles sizing, fees, and accounting.
"""
from dataclasses import dataclass


@dataclass
class Signal:
    action: str          # "BUY" | "SELL" | "HOLD"
    size: float = 1.0    # fraction of available capital (0..1) for entries


class Strategy:
    #: default parameters; override per subclass
    params: dict = {}
    #: optional UI/validation hints per param, e.g.
    #: [{"name": "fast", "label": "fast SMA", "type": "int", "min": 2, "max": 100, "step": 1}]
    #: If omitted, a spec is auto-derived from `params` defaults.
    param_spec: list = []

    def __init__(self, params: dict | None = None):
        merged = dict(self.__class__.params)
        if params:
            merged.update(params)
        self.params = merged

    def on_bar(self, i: int, bars: list[dict]) -> "Signal | None":
        """Return a Signal for bar index i, or None to hold. Override this."""
        raise NotImplementedError
