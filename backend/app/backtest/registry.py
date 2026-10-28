"""Dynamic strategy loading for the backtester.

Only modules under the `strategies.` package may be loaded. The module is
(re)imported fresh so strategies authored at runtime (via the MCP) are picked up
without a server restart.
"""
import importlib

from strategies.base import Strategy

ALLOWED_PREFIX = "strategies."


def load_strategy(module_path: str, params: dict | None = None) -> Strategy:
    if not module_path.startswith(ALLOWED_PREFIX):
        raise ValueError("strategy module must be under the 'strategies.' package")
    mod = importlib.import_module(module_path)
    mod = importlib.reload(mod)
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
            return obj(params)
    raise ValueError(f"no Strategy subclass found in {module_path}")
