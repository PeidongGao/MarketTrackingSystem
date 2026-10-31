const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const local = path.join(__dirname, '../src/market_tracking/web/dashboard.js');
const dashboard = require(fs.existsSync(local) ? local : '../assets/market/dashboard.js');
const header = 'week_ending,ticker,drawdown,week_over_week';
const data = [
  ['2026-08-28','VOO',-.02,.01], ['2026-08-28','QQQ',-.03,.02], ['2026-08-28','SMH',-.1,-.04],
  ['2026-09-25','VOO',-.01,.01], ['2026-09-25','QQQ',-.02,.02], ['2026-09-25','SMH',-.15,-.02],
  ['2026-10-30','VOO',-.032931,-.005397], ['2026-10-30','QQQ',-.094867,-.019747], ['2026-10-30','SMH',-.222288,-.008934],
];
const csv = [header, ...data.map(r => r.join(','))].join('\n');
const reports = dashboard.parseHistory(csv);

test('keeps signed decimal ratios and chronological observations', () => {
  assert.equal(reports.length, 3);
  assert.equal(reports[2].rows[0].drawdown, -.032931);
  assert.equal(dashboard.percent(-.019747), '−1.97%');
  assert.equal(dashboard.percent(.01), '+1.00%');
});
test('arbitrary date range is inclusive and never recalculates recorded drawdowns', () => {
  const selected = dashboard.selectReports(reports, '2026-09-01', '2026-10-30');
  assert.equal(selected.length, 2);
  assert.equal(selected[1].rows[2].drawdown, -.222288);
  assert.equal(dashboard.selectReports(reports, '2026-10-30', '2026-10-30').length, 1);
  assert.equal(dashboard.selectReports(reports, '2026-10-01', '2026-10-02').length, 0);
  assert.throws(() => dashboard.selectReports(reports, '2026-10-30', '2026-08-01'));
});
test('calendar presets anchor to latest recorded week and clamp to available history', () => {
  assert.deepEqual(dashboard.presetRange(reports, '1m'), ['2026-09-30', '2026-10-30']);
  assert.deepEqual(dashboard.presetRange(reports, '3m'), ['2026-08-28', '2026-10-30']);
  assert.deepEqual(dashboard.presetRange(reports, 'ytd'), ['2026-08-28', '2026-10-30']);
});
test('rejects corrupt dates, missing/blank/nonfinite values, duplicates and incomplete weeks', () => {
  for (const invalid of [csv.replace('2026-08-28', '2026-02-30'), csv.replace('-0.02', 'NaN'), csv.replace('-0.02', ''), csv + '\n' + data[0].join(','), csv.split('\n').slice(0, -1).join('\n'), header + '\n']) {
    assert.throws(() => dashboard.parseHistory(invalid));
  }
});
test('selected CSV contains only chosen ETFs and public measurements', () => {
  const result = dashboard.exportCsv(dashboard.selectReports(reports, '2026-10-01', '2026-10-30'), ['QQQ']);
  assert.equal(result, header + '\n2026-10-30,QQQ,-0.094867,-0.019747\n');
  const withPrivate = csv.split('\n').map((line, i) => line + (i ? ',private-value' : ',private_balance')).join('\n');
  assert.ok(!dashboard.exportCsv(dashboard.parseHistory(withPrivate)).includes('private'));
});

test('navigator uses the library-resolved observation bounds, including rounding between weeks', () => {
  assert.deepEqual(dashboard.rangeFromZoom(reports, {start:0,end:81.27,startValue:0,endValue:2}), ['2026-08-28','2026-10-30']);
  assert.deepEqual(dashboard.rangeFromZoom(reports, {startValue:'2026-09-25',endValue:'2026-10-30'}), ['2026-09-25','2026-10-30']);
  assert.deepEqual(dashboard.rangeFromZoom(reports, {start:0,end:100}), ['2026-08-28','2026-10-30']);
});
