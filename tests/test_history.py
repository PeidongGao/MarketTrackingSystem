from datetime import date, datetime
from pathlib import Path
import tempfile
import unittest

from market_tracking.history import append_report, latest_prior_week, load_history
from market_tracking.models import TickerReport


def report(week_ending: date, close: float) -> TickerReport:
    return TickerReport(
        ticker="VOO",
        source="Yahoo Finance",
        source_url="https://finance.yahoo.com/quote/VOO/",
        week_ending=week_ending,
        data_time=datetime(week_ending.year, week_ending.month, week_ending.day, 16),
        close_price=close,
        fifty_two_week_low=500.0,
        fifty_two_week_high=700.0,
        previous_week_close_date=date(2026, 6, 18),
        previous_week_close_price=688.11,
        drawdown=-0.04,
        week_over_week=-0.02,
    )


class HistoryTest(unittest.TestCase):
    def test_append_and_prior_week_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.csv"
            stamp = datetime(2026, 6, 28, 9, 0)
            append_report(path, report(date(2026, 6, 19), 688.11), "close", stamp)
            append_report(path, report(date(2026, 6, 26), 670.26), "close", stamp)

            prior = latest_prior_week(path, "VOO", date(2026, 6, 26))
            self.assertEqual(prior, (date(2026, 6, 19), 688.11))

    def test_upsert_replaces_same_week(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.csv"
            stamp = datetime(2026, 6, 28, 9, 0)
            append_report(path, report(date(2026, 6, 26), 670.26), "close", stamp)
            append_report(path, report(date(2026, 6, 26), 671.00), "close", stamp)

            rows = load_history(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["close"], "671.00")

    def test_no_prior_week_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.csv"
            append_report(path, report(date(2026, 6, 26), 670.26), "close", datetime(2026, 6, 28, 9))
            self.assertIsNone(latest_prior_week(path, "VOO", date(2026, 6, 26)))


if __name__ == "__main__":
    unittest.main()
