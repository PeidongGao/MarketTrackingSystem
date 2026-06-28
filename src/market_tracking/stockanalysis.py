from __future__ import annotations

import json
import time
from datetime import datetime, time as dtime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from market_tracking.config import TIMEZONE
from market_tracking.models import DailyBar, MarketData
from market_tracking.sources import SourceUnavailable

# Independent, no-key source used ONLY to verify Yahoo's reported values.
# Never populates the report. The raw close field ("c") is compared, not the
# adjusted close ("a"), so dividend adjustments do not cause false mismatches.
SOURCE_LABEL = "stockanalysis"
_CLOSE_HOUR = dtime(16, 0)


def _get(url: str, attempts: int = 2, timeout: int = 20) -> dict:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-tracking verify)"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(1.0 * (attempt + 1))
    raise SourceUnavailable(f"stockanalysis request failed: {last_error}")


def fetch_market_data(ticker: str, range_: str = "1M") -> MarketData:
    """Fetch recent daily bars from stockanalysis.com (verification only).

    Tries the ETF path ("e") then the stock path ("s"). A short range is enough
    because this source is used only to confirm the latest and previous-week
    closes, never to compute the 52-week range.
    """
    rows: list[dict] | None = None
    last_error: Exception | None = None
    for kind in ("e", "s"):
        url = (
            f"https://stockanalysis.com/api/symbol/{kind}/{ticker.upper()}"
            f"/history?range={range_}&period=Daily"
        )
        try:
            payload = _get(url)
        except SourceUnavailable as error:
            last_error = error
            continue
        if payload.get("status") == 200 and payload.get("data"):
            rows = payload["data"]
            break
    if rows is None:
        raise SourceUnavailable(f"stockanalysis has no data for {ticker}: {last_error}")

    bars: list[DailyBar] = []
    for row in rows:
        try:
            day = datetime.strptime(str(row["t"])[:10], "%Y-%m-%d").date()
            close = float(row["c"])
            high = float(row["h"])
            low = float(row["l"])
        except (KeyError, ValueError, TypeError):
            continue
        bars.append(
            DailyBar(
                date=day,
                close=close,
                high=high,
                low=low,
                timestamp=datetime.combine(day, _CLOSE_HOUR, TIMEZONE),
            )
        )
    if not bars:
        raise SourceUnavailable(f"stockanalysis returned no usable bars for {ticker}.")

    bars.sort(key=lambda bar: bar.date)
    return MarketData(bars=bars, source=SOURCE_LABEL)


def parse_history(payload: dict) -> MarketData:
    """Parse a stockanalysis history payload into MarketData (test seam)."""
    rows = payload.get("data") or []
    bars: list[DailyBar] = []
    for row in rows:
        try:
            day = datetime.strptime(str(row["t"])[:10], "%Y-%m-%d").date()
            bars.append(
                DailyBar(
                    date=day,
                    close=float(row["c"]),
                    high=float(row["h"]),
                    low=float(row["l"]),
                    timestamp=datetime.combine(day, _CLOSE_HOUR, TIMEZONE),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    if not bars:
        raise SourceUnavailable("stockanalysis payload had no usable bars.")
    bars.sort(key=lambda bar: bar.date)
    return MarketData(bars=bars, source=SOURCE_LABEL)
