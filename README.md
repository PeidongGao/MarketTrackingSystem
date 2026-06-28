# MarketTrackingSystem

A small **weekly** market report generator for `VOO`, `QQQ`, and `SMH`.

It pulls Yahoo Finance daily data only, builds a Markdown report of each
ticker's weekly close, 52-week range, drawdown (DD), and week-over-week (WoW)
change, and validates the report before writing it.

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
| `--basis close\|intraday` | 52-week range basis (default `close`). |
| `--history FILE` / `--no-history` | Append to / skip the time-series at `reports/history.csv`. |
| `--no-validate` | Skip cross-validation. |
| `--strict` | Exit non-zero if any validation check is a **mismatch**. |

## Metrics

```text
DD  = current close / 52-week high - 1
WoW = current close / previous week close - 1
```

The report uses **closing prices only** (`--basis close`). The 52-week high/low
are the max/min of daily *closes* over the trailing 365 days — intraday spikes
are deliberately ignored, matching the project rule "do not use intraday moves."
Pass `--basis intraday` to instead match the range shown on the Yahoo website.

## Usage Boundaries

This repository is intended for low-volume, user-initiated weekly market review.
It is not designed for high-frequency trading, automated market scraping,
investment execution, or bulk redistribution of financial data.

This project does not provide investment, financial, tax, legal, or trading
advice. Read [DISCLAIMER.md](DISCLAIMER.md) before using or publishing generated
reports.

## Cross-validation

Each run records a **Data Validation** section per ticker. Checks:

- **Close & previous-week close** resolved from Yahoo Finance daily chart data.
- **52-week range** is shown on every basis (`close`, `intraday`, Yahoo `meta`)
  so the reported figure is auditable. A `freshness` advisory fires when Yahoo's
  published 52-week extreme drifts from the trailing-window value (stale meta).
- **Reporting week** confirms the run resolved to the requested week.
- **History continuity** confirms this week's previous-week close equals the
  close stored for that week on a prior run — a self-check that strengthens
  over time as `reports/history.csv` grows.

`--strict` turns any `mismatch` into a non-zero exit so CI fails loudly.

## Automation

Two GitHub Actions workflows under `.github/workflows/`:

- **`tests.yml`** — runs the unit tests on every push / PR.
- **`weekly-report.yml`** — runs every Saturday 13:00 UTC (after Friday's
  close), generates the cross-validated report with `--strict`, and commits the
  new `reports/weekly/<date>.md` and updated `reports/history.csv`. Can also be
  run manually (`workflow_dispatch`) for a specific `week_ending`.

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

This is a WillGaoLab project created and maintained by
William (Peidong) Gao.

- Project website: <https://williampeidonggao.com>
- Brand: <https://github.com/WillGaoLab>
- Personal GitHub: <https://github.com/PeidongGao>

```text
William (Peidong) Gao
        |
    WillGaoLab
        |
Open-source Projects
        |
MarketTrackingSystem
```

## Affiliation Disclaimer

This project is not affiliated with, endorsed by, sponsored by, or officially
associated with Yahoo, Yahoo Finance, Vanguard, Invesco, VanEck, Nasdaq, NYSE,
Cboe, any exchange, any ETF issuer, or any other company, organization, fund,
index provider, or service referenced in this repository.

All trademarks, service marks, ticker symbols, fund names, logos, company
names, exchange names, and data-provider names are the property of their
respective owners and are used solely for identification and descriptive
purposes.

## License

Original code and documentation in this repository are available under the
[MIT License](LICENSE). The license does not apply to third-party data,
metadata, names, logos, trademarks, ticker symbols, fund names, or exchange
market data.
