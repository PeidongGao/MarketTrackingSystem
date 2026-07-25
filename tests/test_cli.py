from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from market_tracking.cli import run_report
from market_tracking.models import (
    DailyBar,
    FieldCheck,
    MarketData,
    ValidationReport,
)


def market_data(current_date: date = date(2026, 6, 26)) -> MarketData:
    return MarketData(
        bars=[
            DailyBar(
                date(2025, 6, 10),
                90,
                95,
                85,
                datetime(2025, 6, 10, 16),
            ),
            DailyBar(
                date(2026, 6, 12),
                100,
                105,
                95,
                datetime(2026, 6, 12, 16),
            ),
            DailyBar(
                current_date,
                110,
                115,
                105,
                datetime.combine(current_date, datetime.min.time()).replace(hour=16),
            ),
        ],
        fifty_two_week_low=85,
        fifty_two_week_high=115,
        regular_market_time=datetime.combine(
            current_date, datetime.min.time()
        ).replace(hour=16),
        source="yahoo",
    )


def arguments(tmp: Path, **overrides) -> Namespace:
    values = {
        "week_ending": date(2026, 6, 26),
        "output": tmp / "report.md",
        "output_dir": None,
        "tickers": ["VOO"],
        "basis": "intraday",
        "history": tmp / "history.csv",
        "no_history": False,
        "no_validate": False,
        "no_verify": True,
        "strict": True,
    }
    values.update(overrides)
    return Namespace(**values)


class CliTest(unittest.TestCase):
    def test_strict_mismatch_writes_neither_report_nor_history(self) -> None:
        mismatch = ValidationReport(
            "VOO", [FieldCheck("52-week high (intraday)", {}, "mismatch")]
        )
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            with (
                patch("market_tracking.cli.fetch_market_data", return_value=market_data()),
                patch("market_tracking.cli.cross_validate_ticker", return_value=mismatch),
                redirect_stdout(StringIO()),
                redirect_stderr(StringIO()),
            ):
                status = run_report(arguments(tmp))

            self.assertEqual(status, 1)
            self.assertFalse((tmp / "report.md").exists())
            self.assertFalse((tmp / "history.csv").exists())

    def test_holiday_week_uses_calendar_friday_filename_and_close_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            args = arguments(
                tmp,
                week_ending=date(2026, 6, 19),
                output=None,
                output_dir=tmp,
                no_history=True,
                no_validate=True,
                strict=False,
            )
            with patch(
                "market_tracking.cli.fetch_market_data",
                return_value=market_data(date(2026, 6, 18)),
            ), redirect_stdout(StringIO()):
                status = run_report(args)

            output = tmp / "2026-06-19.md"
            self.assertEqual(status, 0)
            self.assertTrue(output.exists())
            self.assertIn("Close date: 2026-06-18", output.read_text())


if __name__ == "__main__":
    unittest.main()
