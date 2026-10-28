import pytest

from app.api.trades import realized_pl


def test_long_win():
    pl, pct = realized_pl("BUY", 100.0, 110.0, 2.0)
    assert pl == pytest.approx(20.0)
    assert pct == pytest.approx(10.0)


def test_long_loss():
    pl, pct = realized_pl("BUY", 100.0, 90.0, 2.0)
    assert pl == pytest.approx(-20.0)
    assert pct == pytest.approx(-10.0)


def test_short_win():
    # SHORT profits when exit < entry
    pl, pct = realized_pl("SELL", 100.0, 90.0, 2.0)
    assert pl == pytest.approx(20.0)
    assert pct == pytest.approx(10.0)


def test_short_loss():
    pl, pct = realized_pl("SELL", 100.0, 110.0, 2.0)
    assert pl == pytest.approx(-20.0)
    assert pct == pytest.approx(-10.0)


def test_zero_entry_is_safe():
    pl, pct = realized_pl("BUY", 0.0, 10.0, 1.0)
    assert pct == 0.0
