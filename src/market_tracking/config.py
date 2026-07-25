from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TICKERS = ("VOO", "QQQ", "SMH")
SOURCE_NAME = "Yahoo Finance"
TIMEZONE = ZoneInfo("America/New_York")

# Number of calendar days in the trailing "52-week" window.
FIFTY_TWO_WEEK_DAYS = 365

# Basis for the drawdown denominator. Reports always show both the standard
# intraday range and the close-only range. "intraday" matches Yahoo Finance.
FIFTY_TWO_WEEK_BASIS = "intraday"

# Relative tolerance for treating two sources' prices as agreeing (0.1%).
CROSS_SOURCE_TOLERANCE = 0.001

# Default location of the appended time-series used for week-over-week
# continuity cross-checks.
HISTORY_PATH = Path("reports/history.csv")


def source_url(ticker: str) -> str:
    return f"https://finance.yahoo.com/quote/{ticker.upper()}/"
