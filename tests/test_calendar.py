from datetime import date, datetime
import unittest

from market_tracking.calendar import latest_completed_week_ending, select_weekly_closes
from market_tracking.models import DailyBar


def bar(day: date, close: float) -> DailyBar:
    return DailyBar(day, close, close, close, datetime(2026, 6, day.day))


class CalendarTest(unittest.TestCase):
    def test_latest_completed_week_ending_on_saturday(self) -> None:
        self.assertEqual(latest_completed_week_ending(date(2026, 6, 27)), date(2026, 6, 26))

    def test_latest_completed_week_ending_during_week_uses_previous_friday(self) -> None:
        self.assertEqual(latest_completed_week_ending(date(2026, 6, 24)), date(2026, 6, 19))

    def test_select_weekly_closes_uses_last_trading_day_in_holiday_week(self) -> None:
        current, previous = select_weekly_closes(
            [
                bar(date(2026, 6, 18), 100),
                bar(date(2026, 6, 22), 101),
                bar(date(2026, 6, 23), 102),
                bar(date(2026, 6, 24), 103),
                bar(date(2026, 6, 25), 104),
            ],
            date(2026, 6, 26),
        )

        self.assertEqual(current.date, date(2026, 6, 25))
        self.assertEqual(previous.date, date(2026, 6, 18))
