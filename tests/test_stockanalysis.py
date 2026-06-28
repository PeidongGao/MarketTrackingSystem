import unittest

from market_tracking.sources import SourceUnavailable
from market_tracking.stockanalysis import parse_history

# Mirrors the real stockanalysis.com history payload: "c" is the raw close,
# "a" is the dividend/split-adjusted close. Verification must use "c".
PAYLOAD = {
    "status": 200,
    "data": [
        {"t": "2026-06-26", "o": 669.96, "h": 676.955, "l": 668.1, "c": 670.26, "a": 670.26},
        {"t": "2026-06-25", "o": 681.14, "h": 681.54, "l": 672.58, "c": 675.71, "a": 673.7478},
    ],
}


class StockAnalysisParseTest(unittest.TestCase):
    def test_parses_raw_close_sorted(self) -> None:
        data = parse_history(PAYLOAD)
        self.assertEqual(data.source, "stockanalysis")
        self.assertEqual([bar.date.isoformat() for bar in data.bars],
                         ["2026-06-25", "2026-06-26"])  # sorted ascending
        self.assertEqual(data.bars[-1].close, 670.26)

    def test_uses_raw_close_not_adjusted(self) -> None:
        data = parse_history(PAYLOAD)
        june_25 = next(bar for bar in data.bars if bar.date.isoformat() == "2026-06-25")
        self.assertEqual(june_25.close, 675.71)  # raw "c", not adjusted "a" (673.7478)

    def test_empty_payload_raises_unavailable(self) -> None:
        with self.assertRaises(SourceUnavailable):
            parse_history({"status": 200, "data": []})


if __name__ == "__main__":
    unittest.main()
