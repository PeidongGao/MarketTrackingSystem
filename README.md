# MarketTrackingSystem

A small **weekly** market report generator for `VOO`, `QQQ`, and `SMH`.

It pulls Yahoo Finance daily data for every reported value, builds a Markdown
report of each ticker's weekly close, standard Yahoo-style 52-week range,
close-only 52-week range, drawdown (DD), and week-over-week (WoW) change. It
validates the complete report before writing any files.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

Generate the latest completed weekly report (prints to stdout):

```bash
market-tracking report
```

Write a specific week to the standard location and update the history file:

```bash
market-tracking report --week-ending 2026-06-26 \
  --output-dir reports/weekly --history reports/history.csv
```

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--week-ending YYYY-MM-DD` | Report a specific week (default: latest completed week). |
| `--output FILE` / `--output-dir DIR` | Write to an exact file, or to `DIR/<week-ending>.md`. |
| `--tickers VOO QQQ ...` | Override the ticker list. |
| `--basis intraday\|close` | DD high basis (default `intraday`); both ranges are always shown. |
| `--history FILE` / `--no-history` | Append to / skip the time-series at `reports/history.csv`. |
| `--no-validate` | Skip all validation. |
| `--no-verify` | Skip only the independent second-source cross-check. |
| `--strict` | Exit non-zero if any validation check is a **mismatch**. |

## Metrics

```text
DD  = current close / selected 52-week high - 1
WoW = current close / previous week close - 1
```

Every report displays two explicitly labeled ranges over the trailing 365 days:

- **52-week range (Yahoo/intraday)** — minimum daily low and maximum daily high;
  this matches Yahoo's displayed 52-week range and is the default DD basis.
- **52-week closing range** — minimum and maximum daily close; use
  `--basis close` when this should be the DD basis.

Weekly close and WoW always use closing prices. The tool refuses to calculate a
range unless the source response covers the full trailing window.

## Disclaimer

This tool is for **low-volume, user-initiated** weekly market review only — not
high-frequency trading, automated scraping, investment execution, or bulk
redistribution of data. It provides **no investment, financial, tax, legal, or
trading advice**, and is **not affiliated with** Yahoo, any exchange, or any ETF
issuer.

Read the full **[DISCLAIMER.md](DISCLAIMER.md)** before using or publishing
generated reports.

## Cross-validation

Yahoo Finance produces every **reported** value. Each run independently
re-checks those values and records a **Data Validation** section per ticker:

- **Close & previous-week close** are confirmed against an independent source,
  [stockanalysis.com](https://stockanalysis.com) (raw close, so dividend
  adjustments don't cause false alarms). Two sources agreeing within 0.1% →
  `confirmed`; a disagreement → `mismatch`. The second source is used **only**
  to verify — it never populates the report, and a run is **not** failed merely
  because it is unreachable (then the check degrades to `single-source`).
  Disable it with `--no-verify`.
- **52-week range** is strictly recomputed from the raw daily bars on the
  selected DD basis. A disagreement is a `mismatch`. Both range definitions and
  Yahoo metadata are also displayed for auditability; metadata drift is advisory.
- **Reporting week** confirms the run resolved to the requested week.
- **History continuity** confirms this week's previous-week close equals the
  close stored for that week on a prior run — a self-check that strengthens
  over time as `reports/history.csv` grows.

`--strict` turns any `mismatch` into a non-zero exit so CI fails loudly. Strict
validation happens before report or history files are replaced, and each file is
written atomically.

## Automation

Two GitHub Actions workflows are active in [`.github/workflows/`](.github/workflows/):

- **`tests.yml`** — runs the unit tests on every push / PR.
- **`weekly-report.yml`** — runs every Saturday 13:00 UTC (after Friday's
  close), generates the cross-validated report with `--strict`, and commits the
  new `reports/weekly/<date>.md` and updated `reports/history.csv`. Can also be
  run manually (`workflow_dispatch`) for a specific `week_ending`.

Manual dates must be completed calendar Fridays. Holiday weeks retain the
calendar Friday as `Week ending` and record the actual final trading session
separately as `Close date`.

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Repository Strategy

- Canonical code repository:
  <https://github.com/PeidongGao/MarketTrackingSystem>
- WillGaoLab brand:
  <https://github.com/WillGaoLab>
- WilliamGaoWeb project display:
  <https://github.com/PeidongGao/WilliamGaoWeb>

The canonical repository is maintained through William Gao's personal GitHub
account. WillGaoLab is a separate public-facing brand.

## Publishing Workflow

Before editing:

```bash
git pull --ff-only origin main
```

After editing and checking locally:

```bash
git status
git add .
git commit -m "Describe the market tracking update"
git push origin main
```

## Attribution

A **WillGaoLab** project, created and maintained by **William (Peidong) Gao**.

- Project website: <https://williampeidonggao.com>
- Brand: <https://github.com/WillGaoLab>
- Personal GitHub: <https://github.com/PeidongGao>

```text
William (Peidong) Gao
        │
     WillGaoLab
        │
 Open-source projects
        │
 MarketTrackingSystem
```

## Affiliation

Not affiliated with, endorsed by, or sponsored by Yahoo, Yahoo Finance,
stockanalysis.com, Vanguard, Invesco, VanEck, Nasdaq, NYSE, Cboe, any exchange,
any ETF issuer, or any other entity referenced here. All trademarks, ticker symbols, fund names,
and data-provider names are the property of their respective owners and are used
for identification only.

Full text: [DISCLAIMER.md → Affiliation Disclaimer](DISCLAIMER.md#affiliation-disclaimer).

## License

Original code and documentation: **[MIT License](LICENSE)** © 2026 William Gao.

The MIT grant covers this project's own source and documentation only. It does
**not** extend to third-party data, market data, metadata, or any names, logos,
trademarks, ticker symbols, or fund names referenced here — those remain the
property of their respective owners.
