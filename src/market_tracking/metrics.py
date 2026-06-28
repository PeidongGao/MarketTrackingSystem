from __future__ import annotations

from datetime import date, timedelta

from market_tracking.config import FIFTY_TWO_WEEK_DAYS
from market_tracking.models import DailyBar


def drawdown(current_price: float, fifty_two_week_high: float) -> float:
    return current_price / fifty_two_week_high - 1


def week_over_week(current_price: float, previous_week_price: float) -> float:
    return current_price / previous_week_price - 1


def fifty_two_week_range(
    bars: list[DailyBar],
    as_of: date,
    basis: str = "close",
    window_days: int = FIFTY_TWO_WEEK_DAYS,
) -> tuple[float, float]:
    """Return (low, high) over the trailing window ending at ``as_of``.

    ``basis`` is "close" (use daily closing prices) or "intraday" (use the
    daily low/high extremes, matching the Yahoo Finance website range).
    """
    window_start = as_of - timedelta(days=window_days)
    window = [bar for bar in bars if window_start <= bar.date <= as_of]
    if not window:
        raise ValueError(f"No bars in the trailing {window_days}-day window ending {as_of}.")

    if basis == "intraday":
        return min(bar.low for bar in window), max(bar.high for bar in window)
    if basis == "close":
        closes = [bar.close for bar in window]
        return min(closes), max(closes)
    raise ValueError(f"Unknown 52-week basis: {basis!r} (expected 'close' or 'intraday').")
