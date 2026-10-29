"""Describe a strategy's parameters for the UI (sliders/toggles/selects).

A strategy may declare an explicit `param_spec`; otherwise one is inferred from
its `params` defaults so authored strategies get controls for free.
"""


def _infer(name, val) -> dict:
    # bool must be checked before int (bool is a subclass of int)
    if isinstance(val, bool):
        return {"name": name, "label": name, "type": "bool", "default": val}
    if isinstance(val, int):
        return {"name": name, "label": name, "type": "int",
                "default": val, "min": 1, "max": max(100, val * 4), "step": 1}
    if isinstance(val, float):
        step = round(max(abs(val), 1.0) / 100, 4) or 0.01
        return {"name": name, "label": name, "type": "float",
                "default": val, "min": 0.0, "max": max(1.0, val * 4), "step": step}
    return {"name": name, "label": name, "type": "str", "default": val}


def describe_params(strategy) -> list[dict]:
    """Return a list of param descriptors for the given Strategy instance."""
    params = strategy.params or {}
    declared = getattr(strategy, "param_spec", None) or []
    if declared:
        out = []
        for item in declared:
            d = dict(item)
            if "default" not in d:
                d["default"] = params.get(d["name"])
            d.setdefault("label", d["name"])
            out.append(d)
        return out
    return [_infer(name, val) for name, val in params.items()]
