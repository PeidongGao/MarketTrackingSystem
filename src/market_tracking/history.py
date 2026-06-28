from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from market_tracking.models import TickerReport

FIELDNAMES = [
    "week_ending",
    "ticker",
    "source",
    "basis",
    "close",
    "previous_week_close_date",
    "previous_week_close",
    "fifty_two_week_low",
    "fifty_two_week_high",
    "drawdown",
    "week_over_week",
    "generated_at",
]


def load_history(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def latest_prior_week(
    path: Path, ticker: str, before_week_ending: date
) -> tuple[date, float] | None:
    """Return (week_ending, close) of the most recent recorded week before the
    given one for ``ticker`` — used to confirm week-over-week continuity."""
    rows = [
        row
        for row in load_history(path)
        if row["ticker"] == ticker.upper()
        and date.fromisoformat(row["week_ending"]) < before_week_ending
    ]
    if not rows:
        return None
    latest = max(rows, key=lambda row: row["week_ending"])
    return date.fromisoformat(latest["week_ending"]), float(latest["close"])


def append_report(
    path: Path, report: TickerReport, basis: str, generated_at: datetime
) -> None:
    """Upsert one ticker-week row (rewriting any existing row for that key)."""
    rows = load_history(path)
    key = (report.ticker, report.week_ending.isoformat())
    rows = [r for r in rows if (r["ticker"], r["week_ending"]) != key]
    rows.append(
        {
            "week_ending": report.week_ending.isoformat(),
            "ticker": report.ticker,
            "source": report.source,
            "basis": basis,
            "close": f"{report.close_price:.2f}",
            "previous_week_close_date": report.previous_week_close_date.isoformat(),
            "previous_week_close": f"{report.previous_week_close_price:.2f}",
            "fifty_two_week_low": f"{report.fifty_two_week_low:.2f}",
            "fifty_two_week_high": f"{report.fifty_two_week_high:.2f}",
            "drawdown": f"{report.drawdown:.6f}",
            "week_over_week": f"{report.week_over_week:.6f}",
            "generated_at": generated_at.isoformat(),
        }
    )
    rows.sort(key=lambda r: (r["week_ending"], r["ticker"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
