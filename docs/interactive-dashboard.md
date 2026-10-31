# Interactive weekly dashboard

The canonical reusable browser component is `src/market_tracking/web/dashboard.js` and `dashboard.css`. The Python `dashboard` command embeds these assets and the pinned ECharts library into one offline HTML file. `--web-assets-dir` copies the same six-file allowlist to a static website; no private history columns, notes or account balances are exported.

## Integration

Use `WeeklyMarketDashboard.parseHistory(csv)` to validate the public weekly CSV, then `WeeklyMarketDashboard.create(element, reports, echarts)` to render it. The initial view and Reset view show the latest calendar month with all three ETFs selected. The All preset shows the full recorded history. The component provides calendar presets, arbitrary inclusive date selection, linked navigation and crosshairs, ETF visibility controls, exact hover and keyboard values, an accessible selected-data table, CSV export and SVG export. Empty ranges and invalid data have explicit states.

Selecting a date range filters recorded observations without rebasing drawdowns or inventing daily data. The cards describe one recorded week, normally the range's last observation; hovering or using arrow keys inspects other weeks. Weekly changes remain the recorded change from the previous reporting session, even when that previous session falls outside the selected view.

The public website loads `assets/data/weekly-market-history.csv` at runtime. Ordinary weekly CSV updates need no chart-code changes. Keep the PNG as a static fallback and a downloadable snapshot. Re-export shared assets whenever changing the component, and verify the local and website copies agree.

The maintained local plotting script also regenerates `dashboard.html` beside its input history when refreshing the PNG. To regenerate only the HTML, run `market-tracking dashboard --history /path/to/history.csv`.

## Sources and third-party code

- [Apache ECharts source](https://github.com/apache/echarts), pinned to [6.1.0](https://github.com/apache/echarts/releases/tag/6.1.0).
- [Official linked financial-chart example](https://github.com/apache/echarts-examples/blob/gh-pages/public/examples/ts/candlestick-brush.ts): reference for linked grids, data zoom and crosshairs. The panel is a new implementation for the existing weekly ETF measurements.
- [Axis documentation](https://echarts.apache.org/handbook/en/concepts/axis/) and [legend documentation](https://echarts.apache.org/handbook/en/concepts/legend/).
- Evaluated [Plotly date-range sliders](https://plotly.com/javascript/range-slider/) and [TradingView synchronized crosshairs](https://tradingview.github.io/lightweight-charts/tutorials/how_to/set-crosshair-position). ECharts was selected for integrated linked charts and the navigator.

The unmodified upstream bundle retains its Apache-2.0 license and NOTICE. `web/vendor.json` records the exact version, upstream URLs and SHA-256 hashes. To update the library, replace the bundle/license/notice from an explicit official release, refresh the manifest, run the Python and JavaScript behavior tests, re-export the website assets, and check the real browser interactions on desktop and mobile.

## Checks

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
node --test tests/dashboard.test.cjs
```

The site also runs the shared JavaScript behavior tests in its normal `npm test` command. Browser verification covers the actual controls, a one-observation range, a range with no observations, reset, ETF toggles, linked slider zoom, hover, downloads, responsive layout, dark mode, and the static fallback after a failed CSV request.
