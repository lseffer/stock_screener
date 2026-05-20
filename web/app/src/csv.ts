import type { Stock } from './types';
import { COLUMN_LABELS } from './columns';

const HEADER_ORDER: (keyof Stock)[] = [
  'isin',
  'company_name',
  'symbol',
  'currency',
  'sector',
  'yahoo_ticker',
  'report_date',
  'market_date',
  'p_score',
  'roic',
  'roic_percentile',
  'ev_ebitda_ratio_inv',
  'ev_ebitda_ratio',
  'magic_formula_score',
  'magic_formula_score_percentile',
  'shareholder_yield_stock',
  'shareholder_yield_dividends',
  'shareholder_yield_total',
  'shareholder_yield_percentile',
  'price_to_sales',
  'price_to_cash_flow',
  'ncav_ratio',
  'price',
  'target_median_price',
  'number_of_analyst_opinions',
  'ebitda',
  'market_cap',
  'market_cap_eur',
  'cap_tier',
  'trailing_pe',
  'forward_pe',
];

function escape(value: unknown): string {
  if (value === null || value === undefined) return '';
  const s = String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function downloadCsv(rows: Stock[], filename = 'nordic_stocks.csv') {
  const header = HEADER_ORDER.map((k) => COLUMN_LABELS[k] ?? String(k)).join(',');
  const body = rows
    .map((r) => HEADER_ORDER.map((k) => escape(r[k])).join(','))
    .join('\n');
  const csv = `${header}\n${body}\n`;
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
