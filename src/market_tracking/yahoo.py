from __future__ import annotations

import json
import time
from datetime import datetime, time as dtime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from market_tracking.config import TIMEZONE
from market_tracking.models import DailyBar, MarketData
from market_tracking.sources import SourceUnavailable

# Two hosts serve identical data; trying both gives transport redundancy.
_HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
SOURCE_LABEL = "yahoo"
_CLOSE_HOUR = dtime(16, 0)


def _get(url: str, attempts: int = 3, timeout: int = 20) -> dict:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = Request(url, headers={"User-Agent": "market-tracking/0.1"})
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    raise SourceUnavailable(f"Yahoo request failed for {url}: {last_error}") from last_error


def fetch_market_data(ticker: str, range_: str = "14mo") -> MarketData:
    params = urlencode({"range": range_, "interval": "1d", "includePrePost": "false"})
    path = f"/v8/finance/chart/{ticker.upper()}?{params}"

    payload: dict | None = None
    last_error: Exception | None = None
    for host in _HOSTS:
        try:
            payload = _get(f"{host}{path}")
            break
        except SourceUnavailable as error:
            last_error = error
    if payload is None:
        raise SourceUnavailable(f"Yahoo unavailable for {ticker}: {last_error}")

    return parse_chart_payload(payload, ticker)


def parse_chart_payload(payload: dict, ticker: str = "") -> MarketData:
    """Convert a Yahoo chart API payload into :class:`MarketData`.

    Separated from the network call so it can be unit-tested with fixtures.
    """
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise SourceUnavailable(f"Yahoo error for {ticker}: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise SourceUnavailable(f"Yahoo returned no result for {ticker}.")

    result = results[0]
    meta = result["meta"]
    timestamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]

    bars: list[DailyBar] = []
    for raw_timestamp, close, high, low in zip(
        timestamps, quote["close"], quote["high"], quote["low"], strict=True
    ):
        if close is None or high is None or low is None:
            continue
        trading_day = datetime.fromtimestamp(raw_timestamp, TIMEZONE).date()
        bars.append(
            DailyBar(
                date=trading_day,
                close=float(close),
                high=float(high),
                low=float(low),
                timestamp=datetime.combine(trading_day, _CLOSE_HOUR, TIMEZONE),
            )
        )
    if not bars:
        raise SourceUnavailable(f"Yahoo returned no usable bars for {ticker}.")

    regular_market_time = meta.get("regularMarketTime")
    return MarketData(
        bars=bars,
        fifty_two_week_low=meta.get("fiftyTwoWeekLow"),
        fifty_two_week_high=meta.get("fiftyTwoWeekHigh"),
        regular_market_time=(
            datetime.fromtimestamp(regular_market_time, TIMEZONE)
            if regular_market_time
            else None
        ),
        source=SOURCE_LABEL,
    )


def fetch_daily_bars(ticker: str, range_: str = "14mo") -> list[DailyBar]:
    return fetch_market_data(ticker, range_).bars
