"""Ensemble: weighted-threshold vote over child strategies.

Each child's BUY/SELL latches a persistent stance (long=1 / flat=0); HOLD keeps
the prior stance. Every bar we compute score = Σ(weight·stance) / Σweight in
0..1 and go long when score >= threshold, flat otherwise. The long/flat engine
only acts on transitions, so emitting BUY/SELL each bar is safe (idempotent).

Configured entirely via params:
    {"threshold": 0.5,
     "components": [{"module": "strategies.rsi", "params": {...}, "weight": 2.0}, ...]}
"""
from strategies.base import Signal, Strategy


class Ensemble(Strategy):
    name = "Combine Strategies"
    description = "Weighted vote of several strategies; long when the weighted long-score meets the threshold."
    params = {"threshold": 0.5, "components": []}
    param_spec = []  # custom UI (combo builder) — no auto-generated controls

    def __init__(self, params=None):
        super().__init__(params)
        from app.backtest.registry import load_strategy  # lazy: avoids import cycle

        self._threshold = float(self.params.get("threshold", 0.5))
        self._children = []
        self._weights = []
        for c in (self.params.get("components") or []):
            module = c.get("module")
            if not module:
                continue
            try:
                child = load_strategy(module, c.get("params") or {})
            except Exception:
                continue
            self._children.append(child)
            self._weights.append(float(c.get("weight", 1.0)))
        self._total_w = sum(self._weights)
        self._stances = [0.0] * len(self._children)

    def on_bar(self, i, bars):
        if not self._children or self._total_w <= 0:
            return None
        for idx, child in enumerate(self._children):
            sig = child.on_bar(i, bars)
            if sig is not None:
                action = sig.action.upper()
                if action == "BUY":
                    self._stances[idx] = 1.0
                elif action == "SELL":
                    self._stances[idx] = 0.0
                # HOLD / None -> keep previous stance
        score = sum(w * s for w, s in zip(self._weights, self._stances)) / self._total_w
        return Signal("BUY") if score >= self._threshold else Signal("SELL")
