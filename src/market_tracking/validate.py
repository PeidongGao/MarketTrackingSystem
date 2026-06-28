from __future__ import annotations

from datetime import date, timedelta

from market_tracking.calendar import select_weekly_closes
from market_tracking.config import CROSS_SOURCE_TOLERANCE
from market_tracking.metrics import fifty_two_week_range
from market_tracking.models import FieldCheck, MarketData, TickerReport, ValidationReport
from market_tracking.yahoo import SOURCE_LABEL as YAHOO_SOURCE


def _agree(values: list[float], tolerance: float) -> bool:
    if len(values) < 2:
        return True
    low, high = min(values), max(values)
    return (high - low) <= tolerance * max(abs(high), abs(low), 1e-9)


def _cross_source_check(
    field: str, values: dict[str, float | None], tolerance: float
) -> FieldCheck:
    present = {name: value for name, value in values.items() if value is not None}
    if not present:
        return FieldCheck(field, values, "unavailable")
    if len(present) == 1:
        return FieldCheck(field, values, "single", "only one source available")
    if _agree(list(present.values()), tolerance):
        return FieldCheck(field, values, "confirmed", f"{len(present)} sources agree")
    return FieldCheck(field, values, "mismatch", "sources disagree beyond tolerance")


def cross_validate_ticker(
    primary_report: TickerReport,
    requested_week_ending: date,
    per_source_data: dict[str, MarketData],
    basis: str,
    tolerance: float = CROSS_SOURCE_TOLERANCE,
    history_prev_close: tuple[date, float] | None = None,
) -> ValidationReport:
    checks: list[FieldCheck] = []

    # --- Close & previous-week close, compared across every available source.
    closes: dict[str, float | None] = {}
    prev_closes: dict[str, float | None] = {}
    for label, data in per_source_data.items():
        try:
            current, previous = select_weekly_closes(data.bars, requested_week_ending)
            closes[label] = current.close
            prev_closes[label] = previous.close
        except ValueError:
            closes[label] = None
            prev_closes[label] = None
    checks.append(_cross_source_check("close price", closes, tolerance))
    checks.append(_cross_source_check("previous-week close", prev_closes, tolerance))

    # --- 52-week range: surface every basis so the reported value is auditable.
    primary = per_source_data.get(YAHOO_SOURCE) or next(iter(per_source_data.values()))
    as_of = primary_report.week_ending
    close_low, close_high = fifty_two_week_range(primary.bars, as_of, basis="close")
    intra_low, intra_high = fifty_two_week_range(primary.bars, as_of, basis="intraday")
    checks.append(
        FieldCheck(
            "52-week high",
            {
                "reported": primary_report.fifty_two_week_high,
                "close": close_high,
                "intraday": intra_high,
                "yahoo_meta": primary.fifty_two_week_high,
            },
            "advisory",
            f"reported on '{basis}' basis; values differ by definition",
        )
    )
    checks.append(
        FieldCheck(
            "52-week low",
            {
                "reported": primary_report.fifty_two_week_low,
                "close": close_low,
                "intraday": intra_low,
                "yahoo_meta": primary.fifty_two_week_low,
            },
            "advisory",
            f"reported on '{basis}' basis; values differ by definition",
        )
    )

    # Flag Yahoo's published 52w extreme drifting from the trailing-window value.
    meta_high = primary.fifty_two_week_high
    if meta_high is not None and not _agree([meta_high, intra_high], tolerance):
        checks.append(
            FieldCheck(
                "yahoo 52w-high freshness",
                {"yahoo_meta": meta_high, "trailing_intraday": intra_high},
                "advisory",
                "published 52w high differs from trailing-window extreme (stale meta)",
            )
        )
    meta_low = primary.fifty_two_week_low
    if meta_low is not None and not _agree([meta_low, intra_low], tolerance):
        checks.append(
            FieldCheck(
                "yahoo 52w-low freshness",
                {"yahoo_meta": meta_low, "trailing_intraday": intra_low},
                "advisory",
                "published 52w low differs from trailing-window extreme (stale meta)",
            )
        )

    # --- Reporting-week freshness: did we land within the requested reporting week?
    # On Friday market holidays the actual close is Thursday, while the requested
    # reporting week can still be named by its calendar Friday.
    requested_week_start = requested_week_ending - timedelta(
        days=requested_week_ending.weekday()
    )
    if requested_week_start <= primary_report.week_ending <= requested_week_ending:
        checks.append(
            FieldCheck("reporting week", {}, "confirmed", f"resolved to {primary_report.week_ending}")
        )
    else:
        checks.append(
            FieldCheck(
                "reporting week",
                {},
                "mismatch",
                f"requested {requested_week_ending} but resolved to {primary_report.week_ending}",
            )
        )

    # --- History continuity: last run's close must equal this run's prev close.
    if history_prev_close is not None:
        prev_date, prev_value = history_prev_close
        ok_date = prev_date == primary_report.previous_week_close_date
        ok_value = _agree([prev_value, primary_report.previous_week_close_price], tolerance)
        checks.append(
            FieldCheck(
                "history continuity",
                {
                    "stored_prev_close": prev_value,
                    "report_prev_close": primary_report.previous_week_close_price,
                },
                "confirmed" if (ok_date and ok_value) else "mismatch",
                f"stored week {prev_date} vs report prev {primary_report.previous_week_close_date}",
            )
        )
    else:
        checks.append(
            FieldCheck("history continuity", {}, "single", "no prior week recorded yet")
        )

    return ValidationReport(ticker=primary_report.ticker, checks=checks)
