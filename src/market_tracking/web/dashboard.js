/* Shared by MarketTracking's offline panel and WilliamGaoWeb. MIT licensed. */
(function (global, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else global.WeeklyMarketDashboard = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const TICKERS = ["VOO", "QQQ", "SMH"];
  const NAMES = { VOO: "S&P 500", QQQ: "Nasdaq-100", SMH: "Semiconductors" };
  const COLORS = { VOO: "#15815b", QQQ: "#2878bd", SMH: "#c97919" };
  const FIELDS = ["week_ending", "ticker", "drawdown", "week_over_week"];
  const isDate = (value) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const d = new Date(`${value}T12:00:00Z`);
    return Number.isFinite(+d) && d.toISOString().slice(0, 10) === value;
  };
  const formatDate = (value, short = false) => new Intl.DateTimeFormat("en-US", {
    month: "short", day: "numeric", ...(short ? {} : { year: "numeric" }), timeZone: "UTC",
  }).format(new Date(`${value}T12:00:00Z`));
  const percent = (value, digits = 2) => `${value > 0 ? "+" : value < 0 ? "−" : ""}${Math.abs(value * 100).toFixed(digits)}%`;

  function parseHistory(csv) {
    const lines = csv.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
    const headers = lines.shift().split(",").map((v) => v.trim());
    if (new Set(headers).size !== headers.length || !FIELDS.every((f) => headers.includes(f))) {
      throw new Error("Weekly history is missing required columns or contains duplicate headers.");
    }
    const weeks = new Map();
    for (const line of lines) {
      if (!line.trim()) continue;
      const values = line.split(",").map((v) => v.trim());
      if (values.length !== headers.length) throw new Error("A weekly history row has the wrong number of fields.");
      const row = Object.fromEntries(headers.map((h, i) => [h, values[i]]));
      if (!isDate(row.week_ending) || !TICKERS.includes(row.ticker)) throw new Error("Weekly history contains an invalid date or ETF.");
      for (const field of ["drawdown", "week_over_week"]) {
        if (!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(row[field]) || !Number.isFinite(Number(row[field]))) {
          throw new Error("Weekly history contains a missing or invalid measurement.");
        }
      }
      if (!weeks.has(row.week_ending)) weeks.set(row.week_ending, new Map());
      const week = weeks.get(row.week_ending);
      if (week.has(row.ticker)) throw new Error("Weekly history contains a duplicate date and ETF.");
      week.set(row.ticker, { ticker: row.ticker, drawdown: Number(row.drawdown), week_over_week: Number(row.week_over_week) });
    }
    if (!weeks.size) throw new Error("No weekly observations are available.");
    return [...weeks.keys()].sort().map((date) => {
      if (!TICKERS.every((ticker) => weeks.get(date).has(ticker))) throw new Error(`Weekly observations are incomplete for ${date}.`);
      return { date, rows: TICKERS.map((ticker) => weeks.get(date).get(ticker)) };
    });
  }

  function selectReports(reports, start, end) {
    if (!isDate(start) || !isDate(end)) throw new Error("Choose a valid start and end date.");
    if (start > end) throw new Error("The start date must be on or before the end date.");
    return reports.filter((report) => report.date >= start && report.date <= end);
  }

  function presetRange(reports, preset) {
    const first = reports[0].date, end = reports[reports.length - 1].date;
    if (preset === "all") return [first, end];
    if (preset === "ytd") return [first > `${end.slice(0, 4)}-01-01` ? first : `${end.slice(0, 4)}-01-01`, end];
    const months = { "1m": 1, "3m": 3, "6m": 6 }[preset];
    if (!months) throw new Error("Unknown date preset.");
    const d = new Date(`${end}T12:00:00Z`), day = d.getUTCDate();
    d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() - months);
    const lastDay = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0)).getUTCDate();
    d.setUTCDate(Math.min(day, lastDay));
    const start = d.toISOString().slice(0, 10);
    return [start < first ? first : start, end];
  }

  function rangeFromZoom(reports, zoom) {
    const dates = reports.map((report) => report.date), last = dates.length - 1;
    const index = (value, percent) => {
      const dateIndex = typeof value === "string" ? dates.indexOf(value) : -1;
      const resolved = dateIndex >= 0 ? dateIndex : typeof value === "number" && Number.isFinite(value)
        ? Math.round(value) : Math.round(percent / 100 * last);
      return Math.max(0, Math.min(last, resolved));
    };
    const start = index(zoom.startValue, zoom.start || 0);
    const end = Math.max(start, index(zoom.endValue, zoom.end ?? 100));
    return [dates[start], dates[end]];
  }

  function exportCsv(reports, tickers = TICKERS) {
    return `${FIELDS.join(",")}\n${reports.flatMap((report) => report.rows.filter((r) => tickers.includes(r.ticker)).map((row) => (
      [report.date, row.ticker, row.drawdown, row.week_over_week].join(",")
    ))).join("\n")}\n`;
  }

  function create(root, reports, echarts) {
    if (!reports.length || !echarts) throw new Error("The interactive chart could not be loaded.");
    root.hidden = false;
    root.classList.add("market-explorer");
    root.innerHTML = `
      <div class="me-top"><div><span class="me-eyebrow">WEEKLY ETF EXPLORER</span><p class="me-range" data-range></p></div>
        <button type="button" class="me-quiet" data-reset>Reset view</button></div>
      <div class="me-presets" role="group" aria-label="Date range presets">
        <button type="button" data-preset="1m">1M</button><button type="button" data-preset="3m">3M</button>
        <button type="button" data-preset="6m">6M</button><button type="button" data-preset="ytd">YTD</button>
        <button type="button" data-preset="all" aria-pressed="true">All</button></div>
      <form class="me-dates" aria-label="Custom date range">
        <label>From<input type="date" name="from" required></label><span class="me-date-separator" aria-hidden="true">—</span>
        <label>To<input type="date" name="to" required></label><button type="submit">Apply range</button></form>
      <fieldset class="me-etfs"><legend>Compare ETFs</legend>${TICKERS.map((ticker) => (
        `<label><input type="checkbox" value="${ticker}" checked><span class="me-dot" style="background:${COLORS[ticker]}"></span><strong>${ticker}</strong><span class="me-etf-name">${NAMES[ticker]}</span></label>`
      )).join("")}</fieldset>
      <p class="me-observation" data-observation></p>
      <div class="me-cards">${TICKERS.map((ticker) => (
        `<article class="me-card" data-card="${ticker}" style="--series-color:${COLORS[ticker]}"><strong>${ticker}</strong><dl><div><dt>52-week drawdown</dt><dd data-dd></dd></div><div><dt>Weekly change</dt><dd data-wow></dd></div></dl></article>`
      )).join("")}</div>
      <p class="me-message" data-message role="status" aria-live="polite" hidden></p>
      <div class="me-chart" data-chart tabindex="0" aria-label="Weekly drawdown and price changes. Use left and right arrow keys to inspect observations."></div>
      <p class="me-help">Drag the navigator to select a period. Ctrl + scroll or pinch to zoom; drag the chart to pan. Hover or use arrow keys for exact values.</p>
      <div class="me-bottom"><span>Recorded weekly · price changes before dividends</span><div><button type="button" class="me-quiet" data-csv>Export CSV</button><button type="button" class="me-quiet" data-svg>Save chart</button></div></div>
      <details class="me-data"><summary>View data for this range</summary><div class="me-table-wrap"><table><thead><tr><th scope="col">Week ending</th><th scope="col">ETF</th><th scope="col">52-week drawdown</th><th scope="col">Weekly change</th></tr></thead><tbody></tbody></table></div></details>`;

    const query = (s) => root.querySelector(s);
    const from = query('[name="from"]'), to = query('[name="to"]');
    const chartEl = query("[data-chart]"), message = query("[data-message]");
    const csvButton = query("[data-csv]"), svgButton = query("[data-svg]");
    const allDates = reports.map((r) => r.date), byDate = new Map(reports.map((r) => [r.date, r]));
    const selected = Object.fromEntries(TICKERS.map((ticker) => [ticker, true]));
    let visible = reports, focus = reports[reports.length - 1], syncing = false, disposed = false;
    for (const input of [from, to]) { input.min = allDates[0]; input.max = allDates[allDates.length - 1]; }
    const chart = echarts.init(chartEl, null, { renderer: "svg" });
    const activeTickers = () => TICKERS.filter((ticker) => selected[ticker]);
    const colors = () => {
      const dark = document.documentElement.dataset.theme === "dark";
      return dark ? { text: "#dbe3ec", muted: "#9caabb", grid: "#334256", bg: "#182231" }
        : { text: "#263c4c", muted: "#637582", grid: "#e2e8ed", bg: "#ffffff" };
    };
    const showObservation = (report) => {
      focus = report;
      query("[data-observation]").textContent = report ? `Week ending ${formatDate(report.date)}` : "No observation selected";
      for (const ticker of TICKERS) {
        const card = query(`[data-card="${ticker}"]`), row = report && report.rows.find((r) => r.ticker === ticker);
        card.hidden = !selected[ticker];
        card.querySelector("[data-dd]").textContent = row ? percent(row.drawdown) : "—";
        card.querySelector("[data-wow]").textContent = row ? percent(row.week_over_week) : "—";
      }
    };
    const renderTable = () => {
      const body = query("tbody");
      body.replaceChildren(...visible.flatMap((report) => report.rows.filter((r) => selected[r.ticker]).map((row) => {
        const tr = document.createElement("tr");
        for (const value of [formatDate(report.date), row.ticker, percent(row.drawdown), percent(row.week_over_week)]) {
          const td = document.createElement("td"); td.textContent = value; tr.appendChild(td);
        }
        return tr;
      })));
    };
    const setMessage = (text) => { message.hidden = !text; message.textContent = text || ""; };
    const tooltip = (params) => {
      const report = byDate.get(params[0] && params[0].axisValue);
      if (!report) return "";
      return `<strong>${formatDate(report.date)}</strong><br>${report.rows.filter((r) => selected[r.ticker]).map((r) => (
        `${r.ticker}: ${percent(r.drawdown)} drawdown · ${percent(r.week_over_week)} weekly`
      )).join("<br>")}`;
    };
    const option = () => {
      const c = colors();
      return {
        animation: false, backgroundColor: c.bg, textStyle: { fontFamily: "system-ui, sans-serif", color: c.text },
        aria: { enabled: true, description: "Weekly VOO, QQQ and SMH drawdowns and price changes. Exact observations are available in the data table below." },
        title: [{ text: "Drawdown from 52-week high", left: 8, top: 10, textStyle: { color: c.text, fontSize: 14, fontWeight: 500 } },
          { text: "Week-over-week price change", left: 8, top: 272, textStyle: { color: c.text, fontSize: 14, fontWeight: 500 } }],
        legend: { show: false, data: TICKERS, selected: { ...selected } },
        tooltip: { trigger: "axis", confine: true, formatter: tooltip, backgroundColor: c.bg, textStyle: { color: c.text, fontSize: 12 }, borderColor: c.grid },
        axisPointer: { link: [{ xAxisIndex: "all" }], label: { backgroundColor: "#415d72" } },
        grid: [{ left: 58, right: 18, top: 48, height: 174 }, { left: 58, right: 18, top: 310, height: 174 }],
        xAxis: [0, 1].map((index) => ({
          type: "category", data: allDates, gridIndex: index, boundaryGap: false,
          axisLabel: { color: c.muted, hideOverlap: true, formatter: (v) => formatDate(v, true) },
          axisLine: { lineStyle: { color: c.grid } }, axisTick: { show: false }, axisPointer: { type: "line", snap: true },
        })),
        yAxis: [0, 1].map((index) => ({
          type: "value", gridIndex: index, splitNumber: 4,
          min: (e) => Math.min(0, e.min), max: index === 0 ? 0 : (e) => Math.max(0, e.max),
          axisLabel: { color: c.muted, formatter: (v) => `${+(v * 100).toFixed(1)}%` },
          splitLine: { lineStyle: { color: c.grid, type: "dashed" } },
        })),
        dataZoom: [
          { type: "inside", xAxisIndex: [0, 1], filterMode: "filter", zoomOnMouseWheel: "ctrl", moveOnMouseWheel: false, preventDefaultMouseMove: false },
          { type: "slider", xAxisIndex: [0, 1], filterMode: "filter", bottom: 8, height: 28, borderColor: c.grid,
            textStyle: { color: c.muted }, fillerColor: "rgba(40,120,189,0.12)", handleStyle: { color: "#2878bd", borderColor: "#2878bd" },
            labelFormatter: (value, valueStr) => formatDate(valueStr || allDates[Math.round(value)], true) },
        ],
        series: ["drawdown", "week_over_week"].flatMap((metric, index) => TICKERS.map((ticker, tickerIndex) => ({
          id: `${ticker}-${metric}`, name: ticker, type: "line", xAxisIndex: index, yAxisIndex: index,
          data: reports.map((report) => report.rows.find((row) => row.ticker === ticker)[metric]),
          symbol: ["circle", "rect", "triangle"][tickerIndex], symbolSize: 5, showSymbol: true,
          itemStyle: { color: COLORS[ticker] }, lineStyle: { width: 2.5, type: "solid" },
          emphasis: { focus: "series" },
        }))),
      };
    };
    chart.setOption(option());

    const updateRange = (start, end, zoom = true) => {
      try {
        visible = selectReports(reports, start, end);
        if (!visible.length) throw new Error("No weekly observations fall within this range. Include at least one reporting date.");
        if (!activeTickers().length) throw new Error("Select at least one ETF to display the charts.");
        setMessage(""); chartEl.hidden = false; csvButton.disabled = false; svgButton.disabled = false;
        query("[data-range]").textContent = `${formatDate(visible[0].date)} — ${formatDate(visible[visible.length - 1].date)} · ${visible.length} weekly observation${visible.length === 1 ? "" : "s"}`;
        showObservation(visible[visible.length - 1]); renderTable(); chart.resize();
        if (zoom) {
          syncing = true;
          chart.dispatchAction({ type: "dataZoom", startValue: visible[0].date, endValue: visible[visible.length - 1].date });
          syncing = false;
        }
        root.dispatchEvent(new CustomEvent("marketrangechange", { detail: { start, end, count: visible.length } }));
      } catch (error) {
        visible = []; setMessage(error.message); chartEl.hidden = true; csvButton.disabled = true; svgButton.disabled = true;
        query("[data-range]").textContent = "No observations displayed"; showObservation(null); renderTable();
      }
    };
    const setPreset = (preset) => {
      [from.value, to.value] = presetRange(reports, preset);
      root.querySelectorAll("[data-preset]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.preset === preset)));
      updateRange(from.value, to.value);
    };
    query("form").addEventListener("submit", (event) => {
      event.preventDefault(); root.querySelectorAll("[data-preset]").forEach((b) => b.setAttribute("aria-pressed", "false"));
      updateRange(from.value, to.value);
    });
    root.querySelectorAll("[data-preset]").forEach((b) => b.addEventListener("click", () => setPreset(b.dataset.preset)));
    query("[data-reset]").addEventListener("click", () => {
      root.querySelectorAll('[type="checkbox"]').forEach((input) => {
        input.checked = true; selected[input.value] = true;
        chart.dispatchAction({ type: "legendSelect", name: input.value });
      });
      setPreset("1m");
    });
    root.querySelectorAll('[type="checkbox"]').forEach((input) => input.addEventListener("change", () => {
      selected[input.value] = input.checked;
      chart.dispatchAction({ type: input.checked ? "legendSelect" : "legendUnSelect", name: input.value });
      updateRange(from.value, to.value);
    }));
    chart.on("datazoom", () => {
      if (syncing || disposed) return;
      const zoom = chart.getOption().dataZoom[0];
      [from.value, to.value] = rangeFromZoom(reports, zoom);
      root.querySelectorAll("[data-preset]").forEach((b) => b.setAttribute("aria-pressed", "false"));
      updateRange(from.value, to.value, false);
    });
    chart.on("updateAxisPointer", (event) => {
      const axis = event.axesInfo && event.axesInfo[0];
      const report = axis && reports[Number(axis.value)];
      if (report && visible.includes(report)) showObservation(report);
    });
    chart.getZr().on("globalout", () => { if (visible.length) showObservation(visible[visible.length - 1]); });
    chartEl.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key) || !visible.length) return;
      event.preventDefault();
      let i = visible.indexOf(focus);
      i = event.key === "Home" ? 0 : event.key === "End" ? visible.length - 1 : Math.max(0, Math.min(visible.length - 1, i + (event.key === "ArrowLeft" ? -1 : 1)));
      showObservation(visible[i]);
      chart.dispatchAction({ type: "showTip", seriesIndex: TICKERS.findIndex((t) => selected[t]), dataIndex: reports.indexOf(visible[i]) });
    });
    const download = (href, filename) => {
      const a = document.createElement("a"); a.href = href; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    };
    csvButton.addEventListener("click", () => {
      const url = URL.createObjectURL(new Blob([exportCsv(visible, activeTickers())], { type: "text/csv;charset=utf-8" }));
      download(url, `weekly-market-${from.value}-${to.value}.csv`); setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
    svgButton.addEventListener("click", () => download(chart.getDataURL({ type: "svg", backgroundColor: colors().bg }), `weekly-market-${from.value}-${to.value}.svg`));
    const observer = new ResizeObserver(() => { if (!disposed && !chartEl.hidden) chart.resize(); }); observer.observe(root);
    const themeObserver = new MutationObserver(() => { chart.setOption(option()); updateRange(from.value, to.value); });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    setPreset("1m");
    root.hidden = false;
    chart.resize();
    return { chart, setRange: (start, end) => { from.value = start; to.value = end; updateRange(start, end); },
      dispose: () => { disposed = true; observer.disconnect(); themeObserver.disconnect(); chart.dispose(); } };
  }
  return { TICKERS, isDate, formatDate, percent, parseHistory, selectReports, presetRange, rangeFromZoom, exportCsv, create };
});
