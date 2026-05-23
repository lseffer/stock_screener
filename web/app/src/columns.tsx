import { createColumnHelper } from '@tanstack/react-table';
import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import type { Stock, PresetId, CapTier } from './types';
import { fmtCompact, fmtDecimal, fmtEUR, fmtPercent, fmtPrice, fmtText } from './format';

const ch = createColumnHelper<Stock>();

const num = (key: keyof Stock) => (row: Stock) => {
  const v = row[key];
  return typeof v === 'number' ? v : null;
};

function rankTone(percentile: number): 'top' | 'high' | 'mid' | 'low' | 'bottom' {
  if (percentile >= 80) return 'top';
  if (percentile >= 60) return 'high';
  if (percentile >= 40) return 'mid';
  if (percentile >= 20) return 'low';
  return 'bottom';
}

function RankPill({ percentile }: { percentile: number | null | undefined }) {
  if (percentile === null || percentile === undefined || Number.isNaN(percentile)) return null;
  const fromTop = 100 - percentile;
  // "top 8%" for the head, "bottom 8%" for the tail, neutral middle.
  const label =
    percentile >= 80
      ? `top ${Math.max(1, Math.round(fromTop))}%`
      : percentile <= 20
      ? `bot ${Math.max(1, Math.round(percentile))}%`
      : `p${Math.round(percentile)}`;
  return <span className={`rank-pill rank-${rankTone(percentile)}`}>{label}</span>;
}

function ValueWithRank({
  value,
  formatted,
  percentile,
}: {
  value: number | null | undefined;
  formatted: string;
  percentile: number | null | undefined;
}) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return <span className="muted">–</span>;
  }
  return (
    <span className="value-with-rank">
      <span className="value-with-rank-num">{formatted}</span>
      <RankPill percentile={percentile ?? null} />
    </span>
  );
}

export const PIOTROSKI_CRITERIA: { key: keyof Stock; label: string }[] = [
  { key: 'p_score_1', label: 'Positive ROA' },
  { key: 'p_score_2', label: 'Positive Cash Flow' },
  { key: 'p_score_3', label: 'Improving ROA' },
  { key: 'p_score_4', label: 'Earnings Quality' },
  { key: 'p_score_5', label: 'Lower Leverage' },
  { key: 'p_score_6', label: 'Improving Liquidity' },
  { key: 'p_score_7', label: 'No Share Dilution' },
  { key: 'p_score_8', label: 'Improving Gross Margin' },
  { key: 'p_score_9', label: 'Improving Asset Turnover' },
];

function PiotroskiBreakdown({ stock }: { stock: Stock }) {
  const [open, setOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });

  const updatePos = useCallback(() => {
    if (!btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    setPos({ top: rect.bottom + 6, left: rect.left + rect.width / 2 });
  }, []);

  useEffect(() => {
    if (!open) return;
    updatePos();
    const handler = (e: MouseEvent) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target as Node) &&
        btnRef.current && !btnRef.current.contains(e.target as Node)
      ) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, updatePos]);

  const v = stock.p_score;
  if (v === null || v === undefined) return <span className="muted">–</span>;
  const tone = v >= 7 ? 'good' : v >= 5 ? 'mid' : 'bad';

  return (
    <div className="piotroski-wrap">
      <button
        ref={btnRef}
        className={`pill pill-${tone} pill-clickable`}
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
      >
        {v}
      </button>
      {open && createPortal(
        <div
          ref={popoverRef}
          className="piotroski-popover"
          style={{ top: pos.top, left: pos.left }}
        >
          <div className="piotroski-popover-title">Piotroski F-Score: {v}/9</div>
          <ul className="piotroski-list">
            {PIOTROSKI_CRITERIA.map(({ key, label }) => {
              const pass = stock[key] === 1;
              return (
                <li key={key} className={pass ? 'p-pass' : 'p-fail'}>
                  <span className="p-icon">{pass ? '✓' : '✗'}</span>
                  <span>{label}</span>
                </li>
              );
            })}
          </ul>
        </div>,
        document.body,
      )}
    </div>
  );
}

const CAP_TIER_LABEL: Record<CapTier, string> = {
  large: 'Large',
  mid: 'Mid',
  small: 'Small',
  micro: 'Micro',
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
    cell: (info) => <PiotroskiBreakdown stock={info.row.original} />,
    sortingFn: 'basic',
    size: 110,
  }),
  ch.accessor(num('magic_formula_score'), {
    id: 'magic_formula_score',
    header: 'Magic Formula',
    cell: (info) => (
      <ValueWithRank
        value={info.getValue()}
        formatted={fmtDecimal(info.getValue())}
        percentile={info.row.original.magic_formula_score_percentile}
      />
    ),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 180,
  }),
  ch.accessor(num('roic'), {
    id: 'roic',
    header: 'ROIC',
    cell: (info) => (
      <ValueWithRank
        value={info.getValue()}
        formatted={fmtPercent(info.getValue())}
        percentile={info.row.original.roic_percentile}
      />
    ),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 150,
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
  ch.accessor(num('momentum_score'), {
    id: 'momentum_score',
    header: 'Momentum',
    cell: (info) => (
      <ValueWithRank
        value={info.getValue()}
        formatted={fmtPercent(info.getValue())}
        percentile={info.row.original.momentum_score_percentile}
      />
    ),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 170,
  }),
  ch.accessor(num('return_12_1'), {
    id: 'return_12_1',
    header: '12-1m Return',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 130,
  }),
  ch.accessor(num('return_6m'), {
    id: 'return_6m',
    header: '6m Return',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('return_3m'), {
    id: 'return_3m',
    header: '3m Return',
    cell: (info) => fmtPercent(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 110,
  }),
  ch.accessor(num('value_momentum_score'), {
    id: 'value_momentum_score',
    header: 'Value + Momentum',
    cell: (info) => {
      const v = info.getValue();
      if (v === null || v === undefined || Number.isNaN(v)) {
        return <span className="muted">–</span>;
      }
      return <span className={`rank-pill rank-${rankTone(v)}`}>p{Math.round(v)}</span>;
    },
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 160,
  }),
  ch.accessor(num('shareholder_yield_total'), {
    id: 'shareholder_yield_total',
    header: 'SH Yield (total)',
    cell: (info) => (
      <ValueWithRank
        value={info.getValue()}
        formatted={fmtPercent(info.getValue())}
        percentile={info.row.original.shareholder_yield_percentile}
      />
    ),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 170,
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
  ch.accessor(num('market_cap_eur'), {
    id: 'market_cap_eur',
    header: 'Market Cap (€)',
    cell: (info) => fmtEUR(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 130,
  }),
  ch.accessor('cap_tier', {
    id: 'cap_tier',
    header: 'Cap Tier',
    cell: (info) => {
      const v = info.getValue() as CapTier | null;
      if (!v) return <span className="muted">–</span>;
      return <span className={`cap-tier-pill cap-tier-${v}`}>{CAP_TIER_LABEL[v]}</span>;
    },
    sortingFn: (a, b) => {
      const order: Record<string, number> = { large: 4, mid: 3, small: 2, micro: 1 };
      const av = (a.original.cap_tier as string | null) ?? '';
      const bv = (b.original.cap_tier as string | null) ?? '';
      return (order[av] ?? 0) - (order[bv] ?? 0);
    },
    size: 100,
  }),
  ch.accessor(num('market_cap'), {
    id: 'market_cap',
    header: 'Market Cap (native)',
    cell: (info) => fmtCompact(info.getValue()),
    sortingFn: 'basic',
    sortUndefined: 'last',
    size: 140,
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
  top_picks: {
    label: 'Top Picks',
    visible: [
      'company_name',
      'sector',
      'p_score',
      'magic_formula_score',
      'momentum_score',
      'value_momentum_score',
      'roic',
      'ev_ebitda_ratio',
      'price',
      'market_cap_eur',
      'cap_tier',
    ],
  },
  overview: {
    label: 'Overview',
    visible: [
      'company_name',
      'sector',
      'p_score',
      'magic_formula_score',
      'momentum_score',
      'value_momentum_score',
      'roic',
      'ev_ebitda_ratio',
      'price',
      'market_cap_eur',
      'cap_tier',
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
      'cap_tier',
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
      'market_cap_eur',
      'cap_tier',
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
      'shareholder_yield_total',
      'trailing_pe',
      'cap_tier',
    ],
  },
  momentum: {
    label: 'Momentum',
    visible: [
      'company_name',
      'sector',
      'momentum_score',
      'return_12_1',
      'return_6m',
      'return_3m',
      'value_momentum_score',
      'price',
      'market_cap_eur',
      'cap_tier',
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
