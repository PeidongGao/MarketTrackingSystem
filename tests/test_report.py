from datetime import date, datetime
import unittest

from market_tracking.models import DailyBar
from market_tracking.report import build_ticker_report, render_report


def _bars() -> list[DailyBar]:
    # An earlier, higher close drives the 52-week high on a CLOSE basis, so the
    # intraday spikes (high=130 on 6/26) are intentionally ignored.
    return [
        DailyBar(date(2025, 6, 10), 110, 110, 110, datetime(2025, 6, 10, 16)),
        DailyBar(date(2026, 6, 12), 120, 125, 118, datetime(2026, 6, 12, 16)),
        DailyBar(date(2026, 6, 18), 100, 105, 95, datetime(2026, 6, 18, 16)),
        DailyBar(date(2026, 6, 26), 110, 130, 90, datetime(2026, 6, 26, 16)),
    ]


class ReportTest(unittest.TestCase):
    def test_render_report_shows_both_ranges_with_intraday_default(self) -> None:
        report = build_ticker_report("VOO", _bars(), date(2026, 6, 26))
        rendered = render_report([report])

        self.assertIn("Ticker: VOO", rendered)
        self.assertIn("Source: Yahoo Finance", rendered)
        self.assertIn("Week ending: 2026-06-26", rendered)
        self.assertIn("Close price: 110.00", rendered)
        self.assertIn("Previous week close price: 100.00", rendered)
        self.assertIn("52-week range (Yahoo/intraday): 90.00 - 130.00", rendered)
        self.assertIn("52-week closing range: 100.00 - 120.00", rendered)
        self.assertIn("DD (intraday 52-week high): -15.38%", rendered)
        self.assertIn("WoW: 10.00%", rendered)

    def test_close_basis_changes_dd_but_keeps_both_ranges(self) -> None:
        report = build_ticker_report("VOO", _bars(), date(2026, 6, 26), basis="close")
        self.assertEqual(report.fifty_two_week_high, 120)
        self.assertEqual(report.fifty_two_week_intraday_high, 130)
        self.assertEqual(report.fifty_two_week_close_low, 100)
        self.assertAlmostEqual(report.drawdown, 110 / 120 - 1)

    def test_backdated_report_uses_bar_timestamp_not_latest_market_time(self) -> None:
        latest_market_time = datetime(2026, 6, 26, 16)
        report = build_ticker_report(
            "VOO", _bars(), date(2026, 6, 19), data_time=latest_market_time
        )

        self.assertEqual(report.week_ending, date(2026, 6, 19))
        self.assertEqual(report.close_date, date(2026, 6, 18))
        self.assertEqual(report.data_time, datetime(2026, 6, 18, 16))
