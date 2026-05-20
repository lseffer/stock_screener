import { createColumnHelper } from '@tanstack/react-table';
import type { Stock, PresetId } from './types';
import { fmtCompact, fmtDecimal, fmtPercent, fmtPrice, fmtText } from './format';

const ch = createColumnHelper<Stock>();

const num = (key: keyof Stock) => (row: Stock) => {
  const v = row[key];
  return typeof v === 'number' ? v : null;
};

export const columns = [
  ch.accessor('company_name', {
    id: 'company_name',
    header: 'Company',
    cell: (info) => {
      const row = info.row.original;
      const name = info.getValue() ?? row.isin;
      const symbol = row.symbol ?? row.isin;
      return (
        <a
          href={`https://www.google.com/search?q=${encodeURIComponent(`${name} ${symbol} stock`)}`}
          target="_blank"
          rel="noreferrer"
          className="company-link"
        >
          <span className="company-name">{name}</span>
          <span className="company-sym">{symbol}</span>
        </a>
      );
    },
    size: 220,
    enableHiding: false,
  }),
  ch.accessor('sector', {
    id: 'sector',
    header: 'Sector',
    cell: (info) => fmtText(info.getValue()),
    size: 160,
  }),
  ch.accessor('currency', {
    id: 'currency',
    header: 'Ccy',
    cell: (info) => fmtText(info.getValue()),
    size: 70,
  }),
  ch.accessor(num('p_score'), {
    id: 'p_score',
    header: 'Piotroski',
    cell: (info) => {
      const v = info.getValue();
      if (v === null) return <span className="muted">–</span>;
      const tone = v >= 7 ? 'good' : v >= 5 ? 'mid' : 'bad';
      return <span className={`pill pill-${tone}`}>{v}</span>;
    },
    sortingFn: 'basic',
    size: 110,
  }),
  ch.accessor(num('magic_formula_score'), {
    id: 'magic_formula_score',
    header: 'Magic Formula',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 130,
  }),
  ch.accessor(num('roic'), {
    id: 'roic',
    header: 'ROIC',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 100,
  }),
  ch.accessor(num('ev_ebitda_ratio'), {
    id: 'ev_ebitda_ratio',
    header: 'EV/EBITDA',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('ev_ebitda_ratio_inv'), {
    id: 'ev_ebitda_ratio_inv',
    header: 'EBITDA/EV',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('trailing_pe'), {
    id: 'trailing_pe',
    header: 'P/E (TTM)',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 100,
  }),
  ch.accessor(num('forward_pe'), {
    id: 'forward_pe',
    header: 'P/E (fwd)',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 100,
  }),
  ch.accessor(num('price_to_sales'), {
    id: 'price_to_sales',
    header: 'P/Sales',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 100,
  }),
  ch.accessor(num('price_to_cash_flow'), {
    id: 'price_to_cash_flow',
    header: 'P/CF',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 90,
  }),
  ch.accessor(num('shareholder_yield_stock'), {
    id: 'shareholder_yield_stock',
    header: 'SH Yield (stock)',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 140,
  }),
  ch.accessor(num('shareholder_yield_dividends'), {
    id: 'shareholder_yield_dividends',
    header: 'Div Yield',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('ncav_ratio'), {
    id: 'ncav_ratio',
    header: 'NCAV Ratio',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 120,
  }),
  ch.accessor(num('price'), {
    id: 'price',
    header: 'Price',
    cell: (info) => fmtPrice(info.getValue(), info.row.original.currency),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('target_median_price'), {
    id: 'target_median_price',
    header: 'Target',
    cell: (info) => fmtPrice(info.getValue(), info.row.original.currency),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('market_cap'), {
    id: 'market_cap',
    header: 'Market Cap',
    cell: (info) => fmtCompact(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 120,
  }),
  ch.accessor(num('ebitda'), {
    id: 'ebitda',
    header: 'EBITDA',
    cell: (info) => fmtCompact(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('number_of_analyst_opinions'), {
    id: 'number_of_analyst_opinions',
    header: 'Analysts',
    cell: (info) => fmtDecimal(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 100,
  }),
  ch.accessor('report_date', {
    id: 'report_date',
    header: 'Report',
    cell: (info) => fmtText(info.getValue()),
    size: 110,
  }),
  ch.accessor('market_date', {
    id: 'market_date',
    header: 'Market',
    cell: (info) => fmtText(info.getValue()),
    size: 110,
  }),
];

export const ALL_COLUMN_IDS = columns.map((c) => c.id as string);

export const presets: Record<PresetId, { label: string; visible: string[] }> = {
  overview: {
    label: 'Overview',
    visible: [
      'company_name',
      'sector',
      'p_score',
      'magic_formula_score',
      'roic',
      'ev_ebitda_ratio',
      'price',
      'market_cap',
    ],
  },
  piotroski: {
    label: 'Piotroski',
    visible: [
      'company_name',
      'sector',
      'p_score',
      'roic',
      'trailing_pe',
      'forward_pe',
      'price',
    ],
  },
  magic: {
    label: 'Magic Formula',
    visible: [
      'company_name',
      'sector',
      'magic_formula_score',
      'roic',
      'ev_ebitda_ratio',
      'ev_ebitda_ratio_inv',
      'market_cap',
    ],
  },
  value: {
    label: 'Value',
    visible: [
      'company_name',
      'sector',
      'price_to_sales',
      'price_to_cash_flow',
      'ncav_ratio',
      'shareholder_yield_stock',
      'shareholder_yield_dividends',
      'trailing_pe',
    ],
  },
  all: {
    label: 'All metrics',
    visible: ALL_COLUMN_IDS,
  },
};

export function visibilityForPreset(preset: PresetId): Record<string, boolean> {
  const visible = new Set(presets[preset].visible);
  const out: Record<string, boolean> = {};
  for (const id of ALL_COLUMN_IDS) {
    out[id] = visible.has(id);
  }
  return out;
}

export const COLUMN_LABELS: Record<string, string> = Object.fromEntries(
  columns.map((c) => [c.id as string, typeof c.header === 'string' ? c.header : (c.id as string)]),
);
