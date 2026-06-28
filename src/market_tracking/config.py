from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TICKERS = ("VOO", "QQQ", "SMH")
SOURCE_NAME = "Yahoo Finance"
TIMEZONE = ZoneInfo("America/New_York")

# Number of calendar days in the trailing "52-week" window.
FIFTY_TWO_WEEK_DAYS = 365

# Basis for the 52-week high/low and the drawdown denominator.
# "close" uses daily closing prices (honors the project rule "do not use
# intraday price moves"). "intraday" uses daily high/low extremes (matches
# what the Yahoo Finance website displays as the 52-week range).
FIFTY_TWO_WEEK_BASIS = "close"

# Relative tolerance for treating two sources' prices as agreeing (0.1%).
CROSS_SOURCE_TOLERANCE = 0.001

# Default location of the appended time-series used for week-over-week
# continuity cross-checks.
HISTORY_PATH = Path("reports/history.csv")


def source_url(ticker: str) -> str:
    return f"https://finance.yahoo.com/quote/{ticker.upper()}/"
