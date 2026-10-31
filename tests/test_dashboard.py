from __future__ import annotations

import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout

from market_tracking.dashboard import public_history_csv, render_dashboard, write_dashboard, export_web_assets, WEB_ASSETS
from market_tracking.cli import main

HEADER = "week_ending,ticker,drawdown,week_over_week,private_balance\n"
ROWS = "2026-10-30,VOO,-0.032931,-0.005397,secret-balance\n2026-10-30,QQQ,-0.094867,-0.019747,secret-balance\n2026-10-30,SMH,-0.222288,-0.008934,secret-balance\n"


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.history = self.root / "history.csv"
        self.history.write_text(HEADER + ROWS)

    def test_projects_only_public_fields_without_changing_history(self):
        before = self.history.read_bytes()
        text = public_history_csv(self.history)
        self.assertNotIn("private_balance", text)
        self.assertNotIn("secret-balance", text)
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["drawdown"], "-0.094867")
        self.assertEqual(self.history.read_bytes(), before)

    def test_rejects_duplicate_incomplete_invalid_date_and_nonfinite_rows(self):
        for invalid in [HEADER + ROWS + ROWS.splitlines()[0] + "\n", HEADER + "\n".join(ROWS.splitlines()[:2]), (HEADER + ROWS).replace("2026-10-30", "2026-02-30"), (HEADER + ROWS).replace("-0.032931", "NaN"), (HEADER + ROWS).replace("-0.032931", "")]:
            with self.subTest(invalid=invalid):
                self.history.write_text(invalid)
                with self.assertRaises(ValueError): public_history_csv(self.history)

    def test_offline_html_has_bundled_code_public_data_and_no_source_paths(self):
        html = render_dashboard(self.history)
        self.assertIn("WeeklyMarketDashboard.create", html)
        self.assertIn('id="weekly-history"', html)
        self.assertNotIn("secret-balance", html)
        self.assertNotIn(str(self.root), html)
        self.assertNotIn("<script src=", html)

    def test_invalid_data_does_not_replace_existing_panel(self):
        output = self.root / "dashboard.html"
        output.write_text("existing panel")
        self.history.write_text(HEADER + ROWS.splitlines()[0])
        with self.assertRaises(ValueError): write_dashboard(self.history, output)
        self.assertEqual(output.read_text(), "existing panel")

    def test_refuses_to_overwrite_history_and_exports_only_static_allowlist(self):
        with self.assertRaises(ValueError): write_dashboard(self.history, self.history)
        target = self.root / "web"
        export_web_assets(target)
        self.assertEqual({p.name for p in target.iterdir()}, set(WEB_ASSETS))
        self.assertNotIn("history.csv", {p.name for p in target.iterdir()})

    def test_dashboard_cli_writes_local_panel_from_existing_data(self):
        output = self.root / "panel.html"
        with patch("sys.argv", ["market-tracking", "dashboard", "--history", str(self.history), "--output", str(output)]), redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main()
        self.assertEqual(result.exception.code, 0)
        self.assertIn("WeeklyMarketDashboard.create", output.read_text())
