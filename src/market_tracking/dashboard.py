"""Validated, offline interactive weekly dashboard and shared website assets."""
from __future__ import annotations

import csv
import io
import json
import math
import re
from datetime import date
from importlib.resources import files
from pathlib import Path

FIELDS = ("week_ending", "ticker", "drawdown", "week_over_week")
TICKERS = ("VOO", "QQQ", "SMH")
WEB_ASSETS = ("dashboard.js", "dashboard.css", "echarts.min.js", "ECHARTS-LICENSE.txt", "ECHARTS-NOTICE.txt", "vendor.json")


def public_history_csv(history: Path) -> str:
    """Validate all records before exposing only the four public measurements."""
    with history.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or not set(FIELDS).issubset(headers):
            raise ValueError("History is missing required columns or contains duplicate headers.")
        rows = list(reader)
    if not rows:
        raise ValueError("No weekly observations are available.")
    keys: set[tuple[str, str]] = set()
    weeks: dict[str, set[str]] = {}
    for row in rows:
        if None in row or any(row.get(field) is None for field in FIELDS):
            raise ValueError("A history row has the wrong number of fields.")
        value = row["week_ending"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError(f"Invalid reporting date: {value}")
        date.fromisoformat(value)
        ticker = row["ticker"]
        if ticker not in TICKERS:
            raise ValueError(f"Unexpected ETF: {ticker}")
        key = value, ticker
        if key in keys:
            raise ValueError(f"Duplicate history observation: {value} {ticker}")
        keys.add(key)
        weeks.setdefault(value, set()).add(ticker)
        for field in ("drawdown", "week_over_week"):
            if not re.fullmatch(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?", row[field]) or not math.isfinite(float(row[field])):
                raise ValueError(f"Invalid {field}: {value} {ticker}")
    if any(week != set(TICKERS) for week in weeks.values()):
        raise ValueError("Every reporting date must contain VOO, QQQ and SMH.")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows({field: row[field] for field in FIELDS} for row in sorted(rows, key=lambda r: (r["week_ending"], r["ticker"])))
    return output.getvalue()


def _asset(name: str) -> str:
    return files("market_tracking").joinpath("web", name).read_text(encoding="utf-8")


def render_dashboard(history: Path) -> str:
    """Make a self-contained file with no CDN, server or private source fields."""
    data = json.dumps(public_history_csv(history)).replace("<", "\\u003c")
    script = lambda name: re.sub(r"</script", r"<\\/script", _asset(name), flags=re.I)
    css = _asset("dashboard.css")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weekly Market Explorer · William Gao</title>
<link rel="icon" href="data:,">
<style>body{{margin:0;background:#f4f7fa;color:#263c4c;font-family:system-ui,sans-serif}}main{{max-width:1040px;margin:40px auto;padding:0 18px}}h1{{font-size:28px;letter-spacing:-.03em;margin-bottom:8px}}.intro{{font-size:14px;color:#637582;max-width:68ch}}{css}</style>
</head><body><main><h1>Weekly Market Explorer</h1><p class="intro">Explore VOO, QQQ and SMH over any recorded period. Choose dates, compare ETFs, and inspect the exact weekly measurements.</p>
<div data-market-dashboard></div><noscript>Enable JavaScript to explore this dashboard.</noscript>
<p class="intro">Drawdowns retain each report’s selected 52-week high. Current reports use intraday highs; earlier observations may use closing highs. Selecting a range does not recalculate that basis.</p>
<p class="intro">Personal market observations for education, not investment advice.</p></main>
<script type="application/json" id="weekly-history">{data}</script>
<script>{script("echarts.min.js")}</script><script>{script("dashboard.js")}</script>
<script>try{{WeeklyMarketDashboard.create(document.querySelector('[data-market-dashboard]'),WeeklyMarketDashboard.parseHistory(JSON.parse(document.getElementById('weekly-history').textContent)),echarts);}}catch(error){{document.querySelector('[data-market-dashboard]').textContent='Unable to display the weekly dashboard: '+error.message;}}</script>
</body></html>'''


def write_dashboard(history: Path, output: Path, web_assets_dir: Path | None = None) -> None:
    html = render_dashboard(history)
    if output.resolve() == history.resolve():
        raise ValueError("Dashboard output must not overwrite the source history.")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Reuse the CLI's atomic writer; invalid input never replaces a saved panel.
    from market_tracking.cli import _atomic_write_text
    _atomic_write_text(output, html)
    if web_assets_dir is not None:
        export_web_assets(web_assets_dir)


def export_web_assets(destination: Path) -> None:
    """Export only this allowlist, never working history or private notes."""
    destination.mkdir(parents=True, exist_ok=True)
    for name in WEB_ASSETS:
        source = files("market_tracking").joinpath("web", name)
        target = destination / name
        if Path(str(source)).resolve() != target.resolve():
            target.write_bytes(source.read_bytes())
