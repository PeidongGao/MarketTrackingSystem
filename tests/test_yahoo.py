import unittest

from market_tracking.sources import SourceUnavailable
from market_tracking.yahoo import parse_chart_payload

# Two New York trading days: Yahoo daily bars are stamped at market open, but
# reports represent closing data, so parsed bar timestamps are normalized to
# 16:00 ET.
PAYLOAD = {
    "chart": {
        "result": [
            {
                "meta": {
                    "fiftyTwoWeekLow": 565.38,
                    "fiftyTwoWeekHigh": 699.15,
                    "regularMarketTime": 1782504000,
                },
                "timestamp": [1782417600, 1782504000],
                "indicators": {
                    "quote": [
                        {
                            "close": [668.0, 670.26],
                            "high": [669.0, 671.0],
                            "low": [666.0, 668.0],
                        }
                    ]
                },
            }
        ]
    }
}


class YahooParseTest(unittest.TestCase):
    def test_parses_bars_and_meta(self) -> None:
        data = parse_chart_payload(PAYLOAD, "VOO")
        self.assertEqual(len(data.bars), 2)
        self.assertEqual(data.bars[-1].close, 670.26)
        self.assertEqual(data.bars[-1].timestamp.hour, 16)
        self.assertEqual(data.fifty_two_week_high, 699.15)
        self.assertEqual(data.source, "yahoo")

    def test_skips_rows_with_missing_values(self) -> None:
        payload = {
            "chart": {
                "result": [
                    {
                        "meta": {},
                        "timestamp": [1782417600, 1782504000],
                        "indicators": {
                            "quote": [{"close": [None, 670.26], "high": [1, 671.0], "low": [1, 668.0]}]
                        },
                    }
                ]
            }
        }
        data = parse_chart_payload(payload, "VOO")
        self.assertEqual(len(data.bars), 1)

    def test_error_payload_raises_unavailable(self) -> None:
        with self.assertRaises(SourceUnavailable):
            parse_chart_payload({"chart": {"error": "Not Found", "result": None}}, "BAD")


if __name__ == "__main__":
    unittest.main()
