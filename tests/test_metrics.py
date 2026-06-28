from datetime import date, datetime
import unittest

from market_tracking.metrics import drawdown, fifty_two_week_range, week_over_week
from market_tracking.models import DailyBar


def bar(day: date, close: float, high: float, low: float) -> DailyBar:
    return DailyBar(day, close, high, low, datetime(day.year, day.month, day.day, 16))


class MetricsTest(unittest.TestCase):
    def test_drawdown(self) -> None:
        self.assertAlmostEqual(drawdown(90, 100), -0.1)

    def test_week_over_week(self) -> None:
        self.assertAlmostEqual(week_over_week(110, 100), 0.1)

    def test_fifty_two_week_range_close_vs_intraday(self) -> None:
        bars = [
            bar(date(2026, 1, 5), 100, 110, 90),
            bar(date(2026, 3, 5), 120, 125, 95),
            bar(date(2026, 6, 26), 115, 130, 80),
        ]
        self.assertEqual(fifty_two_week_range(bars, date(2026, 6, 26), basis="close"), (100, 120))
        self.assertEqual(
            fifty_two_week_range(bars, date(2026, 6, 26), basis="intraday"), (80, 130)
        )

    def test_fifty_two_week_range_excludes_bars_outside_window(self) -> None:
        bars = [
            bar(date(2024, 1, 1), 10, 10, 10),  # >365 days before as_of -> excluded
            bar(date(2026, 5, 1), 200, 205, 195),
            bar(date(2026, 6, 26), 210, 215, 205),
        ]
        low, high = fifty_two_week_range(bars, date(2026, 6, 26), basis="close")
        self.assertEqual((low, high), (200, 210))
