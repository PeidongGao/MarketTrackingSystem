from datetime import date, datetime
import unittest

from market_tracking.models import DailyBar, MarketData
from market_tracking.report import build_ticker_report
from market_tracking.validate import cross_validate_ticker


def bars(close_2618: float, close_2626: float) -> list[DailyBar]:
    return [
        DailyBar(date(2026, 6, 12), 120, 125, 118, datetime(2026, 6, 12, 16)),
        DailyBar(date(2026, 6, 18), close_2618, close_2618, close_2618, datetime(2026, 6, 18, 16)),
        DailyBar(date(2026, 6, 26), close_2626, close_2626, close_2626, datetime(2026, 6, 26, 16)),
    ]


class ValidateTest(unittest.TestCase):
    def _report(self):
        return build_ticker_report("VOO", bars(100, 110), date(2026, 6, 26))

    def _check(self, validation, field):
        return next(c for c in validation.checks if c.field == field)

    def test_two_agreeing_sources_confirm(self) -> None:
        per_source = {
            "yahoo": MarketData(bars(100, 110), source="yahoo"),
            "audit": MarketData(bars(100, 110.05), source="audit"),
        }
        validation = cross_validate_ticker(
            self._report(), date(2026, 6, 26), per_source, basis="close", tolerance=0.001
        )
        self.assertTrue(validation.ok)
        self.assertEqual(self._check(validation, "close price").status, "confirmed")

    def test_disagreeing_sources_mismatch(self) -> None:
        per_source = {
            "yahoo": MarketData(bars(100, 110), source="yahoo"),
            "audit": MarketData(bars(100, 150), source="audit"),
        }
        validation = cross_validate_ticker(
            self._report(), date(2026, 6, 26), per_source, basis="close", tolerance=0.001
        )
        self.assertFalse(validation.ok)
        self.assertEqual(self._check(validation, "close price").status, "mismatch")

    def test_single_source_is_not_a_failure(self) -> None:
        per_source = {"yahoo": MarketData(bars(100, 110), source="yahoo")}
        validation = cross_validate_ticker(
            self._report(), date(2026, 6, 26), per_source, basis="close", tolerance=0.001
        )
        self.assertTrue(validation.ok)
        self.assertEqual(self._check(validation, "close price").status, "single")

    def test_history_continuity_mismatch(self) -> None:
        per_source = {"yahoo": MarketData(bars(100, 110), source="yahoo")}
        validation = cross_validate_ticker(
            self._report(),
            date(2026, 6, 26),
            per_source,
            basis="close",
            tolerance=0.001,
            history_prev_close=(date(2026, 6, 18), 999.0),
        )
        self.assertFalse(validation.ok)
        self.assertEqual(self._check(validation, "history continuity").status, "mismatch")

    def test_yahoo_metadata_used_for_range_advisory_even_if_not_first_source(self) -> None:
        per_source = {
            "audit": MarketData(bars(100, 110), source="audit"),
            "yahoo": MarketData(
                bars(100, 110),
                fifty_two_week_low=95.0,
                fifty_two_week_high=125.0,
                source="yahoo",
            ),
        }
        validation = cross_validate_ticker(
            self._report(), date(2026, 6, 26), per_source, basis="close", tolerance=0.001
        )

        self.assertEqual(self._check(validation, "52-week high").values["yahoo_meta"], 125.0)

    def test_friday_holiday_resolved_to_thursday_is_confirmed(self) -> None:
        per_source = {"yahoo": MarketData(bars(100, 110), source="yahoo")}
        report = build_ticker_report("VOO", bars(100, 110), date(2026, 6, 19))
        validation = cross_validate_ticker(
            report, date(2026, 6, 19), per_source, basis="close", tolerance=0.001
        )

        self.assertEqual(report.week_ending, date(2026, 6, 18))
        self.assertTrue(validation.ok)
        self.assertEqual(self._check(validation, "reporting week").status, "confirmed")


if __name__ == "__main__":
    unittest.main()
