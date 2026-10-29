"""Pure technical-indicator helpers for strategies.

Each returns the latest value for the given close/price list in O(n) so a
strategy can call it per bar (and once more on the prior slice for crossovers)
without blowing up the backtest to O(n^3).
"""
from statistics import pstdev


def sma(closes, n):
    return sum(closes[-n:]) / n


def ema(closes, n):
    k = 2.0 / (n + 1)
    e = closes[0]
    for c in closes[1:]:
        e = c * k + e * (1 - k)
    return e


def stddev(vals):
    return pstdev(vals) if len(vals) > 1 else 0.0


def bollinger(closes, n, k):
    """Return (middle, upper, lower) bands for the last n closes."""
    window = closes[-n:]
    mid = sum(window) / n
    sd = stddev(window)
    return mid, mid + k * sd, mid - k * sd


def rsi(closes, n):
    """Simple (non-Wilder) RSI over the last n deltas. None if not enough data."""
    if len(closes) < n + 1:
        return None
    gains = losses = 0.0
    for j in range(len(closes) - n, len(closes)):
        ch = closes[j] - closes[j - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch
    avg_gain = gains / n
    avg_loss = losses / n
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def macd(closes, fast=12, slow=26, signal=9):
    """Return (macd_line, signal_line) latest values, computed in one O(n) pass."""
    if len(closes) < slow + signal:
        return None
    kf = 2.0 / (fast + 1)
    ks = 2.0 / (slow + 1)
    kg = 2.0 / (signal + 1)
    ef = es = closes[0]
    line = []
    for c in closes:
        ef = c * kf + ef * (1 - kf)
        es = c * ks + es * (1 - ks)
        line.append(ef - es)
    sig = line[0]
    for m in line[1:]:
        sig = m * kg + sig * (1 - kg)
    return line[-1], sig
