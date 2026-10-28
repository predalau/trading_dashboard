import pytest

import app.services.strategy_authoring as sa
from app.services.strategy_authoring import create_strategy, validate_strategy_source, StrategyValidationError

VALID = """
from strategies.base import Strategy, Signal

class MyStrat(Strategy):
    params = {"n": 3}
    def on_bar(self, i, bars):
        if i < self.params["n"]:
            return None
        return Signal("BUY")
"""


def test_valid_source_passes():
    validate_strategy_source(VALID)  # no raise


def test_import_os_rejected():
    with pytest.raises(StrategyValidationError):
        validate_strategy_source("import os\n" + VALID)


def test_from_other_module_rejected():
    with pytest.raises(StrategyValidationError):
        validate_strategy_source("from subprocess import run\n" + VALID)


def test_eval_rejected():
    src = VALID.replace('return Signal("BUY")', 'return eval("1+1")')
    with pytest.raises(StrategyValidationError):
        validate_strategy_source(src)


def test_dunder_access_rejected():
    src = VALID.replace('return Signal("BUY")', 'return self.__class__.__bases__')
    with pytest.raises(StrategyValidationError):
        validate_strategy_source(src)


def test_no_strategy_subclass_rejected():
    with pytest.raises(StrategyValidationError):
        validate_strategy_source("x = 1\n")


def test_create_writes_file_and_row(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(sa, "STRATEGIES_DIR", str(tmp_path))
    row = create_strategy(db_session, slug="my_strat", name="My", source=VALID,
                          params={"n": 3}, description="t")
    assert row.module == "strategies.my_strat"
    assert (tmp_path / "my_strat.py").exists()


def test_bad_slug_rejected(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(sa, "STRATEGIES_DIR", str(tmp_path))
    with pytest.raises(StrategyValidationError):
        create_strategy(db_session, slug="Bad-Slug!", name="x", source=VALID)


def test_reserved_slug_rejected(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(sa, "STRATEGIES_DIR", str(tmp_path))
    with pytest.raises(StrategyValidationError):
        create_strategy(db_session, slug="sma_cross", name="x", source=VALID)
