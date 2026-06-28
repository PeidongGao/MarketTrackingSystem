from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from market_tracking.calendar import latest_completed_week_ending
from market_tracking.config import (
    CROSS_SOURCE_TOLERANCE,
    DEFAULT_TICKERS,
    FIFTY_TWO_WEEK_BASIS,
    HISTORY_PATH,
    TIMEZONE,
)
from market_tracking import stockanalysis
from market_tracking.history import append_report, latest_prior_week
from market_tracking.models import TickerReport, ValidationReport
from market_tracking.report import build_ticker_report, render_report
from market_tracking.sources import SourceUnavailable
from market_tracking.validate import cross_validate_ticker
from market_tracking.yahoo import SOURCE_LABEL as YAHOO_SOURCE, fetch_market_data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="market-tracking")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report = subparsers.add_parser("report", help="Generate a weekly Markdown report.")
    report.add_argument("--week-ending", type=date.fromisoformat)
    report.add_argument("--output", type=Path, help="Exact output file path.")
    report.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write '<week-ending>.md' into (filename derived automatically).",
    )
    report.add_argument("--tickers", nargs="+", default=list(DEFAULT_TICKERS))
    report.add_argument("--basis", choices=("close", "intraday"), default=FIFTY_TWO_WEEK_BASIS)
    report.add_argument("--history", type=Path, default=HISTORY_PATH)
    report.add_argument("--no-history", action="store_true", help="Do not read/write history.")
    report.add_argument("--no-validate", action="store_true", help="Skip all validation.")
    report.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the independent second-source (stockanalysis.com) cross-check.",
    )
    report.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any validation check is a mismatch.",
    )
    return parser.parse_args(argv)


def run_report(args: argparse.Namespace) -> int:
    week_ending = args.week_ending or latest_completed_week_ending(
        datetime.now(TIMEZONE).date()
    )
    generated_at = datetime.now(TIMEZONE)
    history_path: Path | None = None if args.no_history else args.history

    reports: list[TickerReport] = []
    validations: dict[str, ValidationReport] = {}

    for ticker in args.tickers:
        primary = fetch_market_data(ticker)
        per_source = {YAHOO_SOURCE: primary}

        # Independent verification source: confirms Yahoo's reported numbers but
        # never populates the report, and never fails the run if unreachable.
        if not args.no_validate and not args.no_verify:
            try:
                per_source[stockanalysis.SOURCE_LABEL] = stockanalysis.fetch_market_data(ticker)
            except SourceUnavailable as error:
                print(
                    f"  note: verification source unavailable for {ticker}: {error}",
                    file=sys.stderr,
                )

        report = build_ticker_report(
            ticker,
            primary.bars,
            week_ending,
            basis=args.basis,
            data_time=primary.regular_market_time,
        )
        reports.append(report)

        if not args.no_validate:
            prior = (
                latest_prior_week(history_path, ticker, report.week_ending)
                if history_path is not None
                else None
            )
            validations[report.ticker] = cross_validate_ticker(
                report,
                week_ending,
                per_source,
                basis=args.basis,
                tolerance=CROSS_SOURCE_TOLERANCE,
                history_prev_close=prior,
            )

    rendered = render_report(reports, validations or None, generated_at)
    resolved_week_ending = reports[0].week_ending if reports else week_ending
    output = args.output or (
        args.output_dir / f"{resolved_week_ending.isoformat()}.md" if args.output_dir else None
    )
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(rendered, end="")

    if history_path is not None:
        for report in reports:
            append_report(history_path, report, args.basis, generated_at)

    mismatched = [
        f"{ticker}: {', '.join(c.field for c in v.mismatches)}"
        for ticker, v in validations.items()
        if not v.ok
    ]
    if mismatched:
        print("VALIDATION MISMATCH -> " + "; ".join(mismatched), file=sys.stderr)
        if args.strict:
            return 1
    return 0


def main() -> None:
    args = parse_args()
    if args.command == "report":
        raise SystemExit(run_report(args))


if __name__ == "__main__":
    main()
