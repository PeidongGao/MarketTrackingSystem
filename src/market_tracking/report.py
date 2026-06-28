from __future__ import annotations

from datetime import date, datetime

from market_tracking.calendar import select_weekly_closes
from market_tracking.config import FIFTY_TWO_WEEK_BASIS, SOURCE_NAME, source_url
from market_tracking.metrics import drawdown, fifty_two_week_range, week_over_week
from market_tracking.models import DailyBar, TickerReport, ValidationReport


def build_ticker_report(
    ticker: str,
    bars: list[DailyBar],
    week_ending: date,
    basis: str = FIFTY_TWO_WEEK_BASIS,
    data_time: datetime | None = None,
) -> TickerReport:
    current, previous = select_weekly_closes(bars, week_ending)
    low, high = fifty_two_week_range(bars, current.date, basis=basis)

    return TickerReport(
        ticker=ticker.upper(),
        source=SOURCE_NAME,
        source_url=source_url(ticker),
        week_ending=current.date,
        data_time=data_time if data_time and data_time.date() == current.date else current.timestamp,
        close_price=current.close,
        fifty_two_week_low=low,
        fifty_two_week_high=high,
        previous_week_close_date=previous.date,
        previous_week_close_price=previous.close,
        drawdown=drawdown(current.close, high),
        week_over_week=week_over_week(current.close, previous.close),
    )


_STATUS_MARK = {
    "confirmed": "OK",
    "single": "single-source",
    "advisory": "note",
    "unavailable": "unavailable",
    "mismatch": "MISMATCH",
}


def render_report(
    reports: list[TickerReport],
    validations: dict[str, ValidationReport] | None = None,
    generated_at: datetime | None = None,
) -> str:
    lines = ["# Weekly Market Tracking Report", ""]
    for report in reports:
        lines.extend(
            [
                f"## {report.ticker}",
                f"Ticker: {report.ticker}",
                f"Source: {report.source}",
                f"Source URL: {report.source_url}",
                "",
                f"Week ending: {report.week_ending.isoformat()}",
                f"Data time: {report.data_time.isoformat()}",
                "",
                f"Close price: {report.close_price:.2f}",
                "",
                f"52-week low: {report.fifty_two_week_low:.2f}",
                f"52-week high: {report.fifty_two_week_high:.2f}",
                (
                    "52-week range: "
                    f"{report.fifty_two_week_low:.2f} - {report.fifty_two_week_high:.2f}"
                ),
                "",
                f"Previous week close date: {report.previous_week_close_date.isoformat()}",
                f"Previous week close price: {report.previous_week_close_price:.2f}",
                "",
                f"DD: {report.drawdown:.2%}",
                f"WoW: {report.week_over_week:.2%}",
                "",
            ]
        )

    if validations:
        lines.extend(_render_validation(reports, validations))

    if generated_at is not None:
        lines.extend([f"_Generated: {generated_at.isoformat()}_", ""])

    return "\n".join(lines).rstrip() + "\n"


def _render_validation(
    reports: list[TickerReport], validations: dict[str, ValidationReport]
) -> list[str]:
    overall_ok = all(validations[r.ticker].ok for r in reports if r.ticker in validations)
    header = "PASS" if overall_ok else "FAIL — review mismatches below"
    lines = ["## Data Validation", "", f"Overall: {header}", ""]
    for report in reports:
        validation = validations.get(report.ticker)
        if validation is None:
            continue
        lines.append(f"### {report.ticker}")
        lines.append("")
        lines.append("| Check | Values | Status |")
        lines.append("| --- | --- | --- |")
        for check in validation.checks:
            values = ", ".join(
                f"{name}={_fmt(value)}" for name, value in check.values.items()
            )
            mark = _STATUS_MARK.get(check.status, check.status)
            detail = f" — {check.detail}" if check.detail else ""
            lines.append(f"| {check.field} | {values}{detail} | {mark} |")
        lines.append("")
    return lines


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"
