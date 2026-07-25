from __future__ import annotations

import csv
import os
from datetime import date, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from market_tracking.models import TickerReport

FIELDNAMES = [
    "week_ending",
    "close_date",
    "ticker",
    "source",
    "basis",
    "range_basis",
    "close",
    "previous_week_close_date",
    "previous_week_close",
    "fifty_two_week_low",
    "fifty_two_week_high",
    "close_52w_low",
    "close_52w_high",
    "intraday_52w_low",
    "intraday_52w_high",
    "drawdown",
    "dd_basis",
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
    close_date = latest.get("close_date") or latest["week_ending"]
    return date.fromisoformat(close_date), float(latest["close"])


def append_report(
    path: Path, report: TickerReport, basis: str, generated_at: datetime
) -> None:
    upsert_reports(path, [report], basis, generated_at)


def upsert_reports(
    path: Path,
    reports: list[TickerReport],
    basis: str,
    generated_at: datetime,
) -> None:
    """Upsert a complete report batch with one atomic history replacement."""
    rows = load_history(path)
    keys = {(report.ticker, report.week_ending.isoformat()) for report in reports}
    rows = [
        row
        for row in rows
        if (row["ticker"], row["week_ending"]) not in keys
    ]
    for report in reports:
        rows.append(
            {
                "week_ending": report.week_ending.isoformat(),
                "close_date": report.close_date.isoformat(),
                "ticker": report.ticker,
                "source": report.source,
                "basis": basis,
                "range_basis": report.range_basis,
                "close": f"{report.close_price:.2f}",
                "previous_week_close_date": report.previous_week_close_date.isoformat(),
                "previous_week_close": f"{report.previous_week_close_price:.2f}",
                "fifty_two_week_low": f"{report.fifty_two_week_low:.2f}",
                "fifty_two_week_high": f"{report.fifty_two_week_high:.2f}",
                "close_52w_low": f"{report.fifty_two_week_close_low:.2f}",
                "close_52w_high": f"{report.fifty_two_week_close_high:.2f}",
                "intraday_52w_low": f"{report.fifty_two_week_intraday_low:.2f}",
                "intraday_52w_high": f"{report.fifty_two_week_intraday_high:.2f}",
                "drawdown": f"{report.drawdown:.6f}",
                "dd_basis": report.range_basis,
                "week_over_week": f"{report.week_over_week:.6f}",
                "generated_at": generated_at.isoformat(),
            }
        )
    rows.sort(key=lambda r: (r["week_ending"], r["ticker"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            temporary = Path(handle.name)
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise
