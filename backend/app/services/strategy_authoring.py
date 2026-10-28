"""Author Python strategies at runtime with an AST allow-list.

NOT a full sandbox — it is defense-in-depth for a single-operator, self-hosted
tool. Strategy source may only import from strategies.base, must define a
Strategy subclass, and may not use dangerous builtins / dunder access. The
backtest worker still executes the code, so only trusted (operator/MCP) callers
may author strategies.
"""
import ast
import os
import re

from sqlalchemy.orm import Session

from app.models import StrategyDef

# backend/app/services/strategy_authoring.py -> backend/strategies
STRATEGIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "strategies"
)

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,50}$")
RESERVED = {"base", "sma_cross", "__init__"}

_FORBIDDEN_NAMES = {
    "__import__", "eval", "exec", "compile", "open", "globals", "locals",
    "getattr", "setattr", "delattr", "vars", "input", "breakpoint", "exit",
    "quit", "memoryview", "os", "sys", "subprocess", "socket", "importlib",
    "builtins", "shutil", "pathlib", "requests", "httpx", "urllib", "pickle",
}


class StrategyValidationError(Exception):
    pass


def validate_strategy_source(source: str) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise StrategyValidationError(f"syntax error: {exc}")

    has_strategy_subclass = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            raise StrategyValidationError(
                "imports are not allowed except 'from strategies.base import ...'"
            )
        if isinstance(node, ast.ImportFrom):
            if node.module != "strategies.base":
                raise StrategyValidationError(
                    f"import from '{node.module}' not allowed (only strategies.base)"
                )
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                raise StrategyValidationError(f"dunder attribute access not allowed: {node.attr}")
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise StrategyValidationError(f"use of '{node.id}' is not allowed")
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Strategy":
                    has_strategy_subclass = True

    if not has_strategy_subclass:
        raise StrategyValidationError("source must define a class subclassing Strategy")


def create_strategy(db: Session, *, slug: str, name: str, source: str,
                    params: dict | None = None, description: str | None = None,
                    strategies_dir: str | None = None) -> StrategyDef:
    if not SLUG_RE.match(slug):
        raise StrategyValidationError("slug must be lowercase [a-z0-9_], 2-51 chars, starting with a letter")
    if slug in RESERVED:
        raise StrategyValidationError(f"'{slug}' is a reserved strategy name")
    validate_strategy_source(source)

    sdir = strategies_dir or STRATEGIES_DIR
    os.makedirs(sdir, exist_ok=True)
    with open(os.path.join(sdir, f"{slug}.py"), "w") as f:
        f.write(source)

    module = f"strategies.{slug}"
    row = db.query(StrategyDef).filter(StrategyDef.slug == slug).first()
    if row:
        row.name, row.module, row.params, row.description = name, module, params or {}, description
    else:
        row = StrategyDef(slug=slug, name=name, module=module, params=params or {}, description=description)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
