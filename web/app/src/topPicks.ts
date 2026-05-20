import type { Stock } from './types';

export const TOP_PICKS_PER_BUCKET = 5;

export type BucketId = 'quality' | 'value' | 'deep_value';

export type MetricType = 'pct' | 'num' | 'score';

export interface PickMetric {
  key: keyof Stock;
  label: string;
  type: MetricType;
}

export interface PickBucket {
  id: BucketId;
  title: string;
  description: string;
  picks: Stock[];
  primary: PickMetric;
  secondary: PickMetric;
}

const QUALITY_MIN_P_SCORE = 7;
const QUALITY_MIN_ROIC = 0.1;
const VALUE_MIN_P_SCORE = 5;
const DEEP_VALUE_MIN_P_SCORE = 5;
const DEEP_VALUE_MAX_PE = 10;

function num(v: number | null | undefined): number | null {
  return typeof v === 'number' && !Number.isNaN(v) ? v : null;
}

function quality(rows: Stock[]): Stock[] {
  return rows
    .filter((r) => {
      const p = num(r.p_score);
      const roic = num(r.roic);
      return p !== null && p >= QUALITY_MIN_P_SCORE && roic !== null && roic > QUALITY_MIN_ROIC;
    })
    .sort((a, b) => {
      const ra = num(a.roic) ?? -Infinity;
      const rb = num(b.roic) ?? -Infinity;
      if (rb !== ra) return rb - ra;
      const pa = num(a.p_score) ?? -Infinity;
      const pb = num(b.p_score) ?? -Infinity;
      return pb - pa;
    })
    .slice(0, TOP_PICKS_PER_BUCKET);
}

function value(rows: Stock[]): Stock[] {
  return rows
    .filter((r) => {
      const mf = num(r.magic_formula_score);
      const p = num(r.p_score);
      const roic = num(r.roic);
      return (
        mf !== null &&
        p !== null &&
        p >= VALUE_MIN_P_SCORE &&
        roic !== null &&
        roic > 0
      );
    })
    .sort((a, b) => {
      const ma = num(a.magic_formula_score) ?? -Infinity;
      const mb = num(b.magic_formula_score) ?? -Infinity;
      return mb - ma;
    })
    .slice(0, TOP_PICKS_PER_BUCKET);
}

function deepValue(rows: Stock[]): Stock[] {
  return rows
    .filter((r) => {
      const ncav = num(r.ncav_ratio);
      const pe = num(r.trailing_pe);
      const p = num(r.p_score);
      const ncavMatch = ncav !== null && ncav > 1;
      const peMatch =
        pe !== null &&
        pe > 0 &&
        pe <= DEEP_VALUE_MAX_PE &&
        p !== null &&
        p >= DEEP_VALUE_MIN_P_SCORE;
      return ncavMatch || peMatch;
    })
    .sort((a, b) => {
      const na = num(a.ncav_ratio);
      const nb = num(b.ncav_ratio);
      const aHasNcav = na !== null && na > 1;
      const bHasNcav = nb !== null && nb > 1;
      if (aHasNcav && bHasNcav) return (nb ?? 0) - (na ?? 0);
      if (aHasNcav) return -1;
      if (bHasNcav) return 1;
      const pea = num(a.trailing_pe) ?? Infinity;
      const peb = num(b.trailing_pe) ?? Infinity;
      return pea - peb;
    })
    .slice(0, TOP_PICKS_PER_BUCKET);
}

export function computeTopPicks(rows: Stock[]): PickBucket[] {
  return [
    {
      id: 'quality',
      title: 'Quality',
      description: 'Strong fundamentals: Piotroski F-Score ≥ 7 with ROIC above 10%.',
      picks: quality(rows),
      primary: { key: 'roic', label: 'ROIC', type: 'pct' },
      secondary: { key: 'p_score', label: 'F-Score', type: 'score' },
    },
    {
      id: 'value',
      title: 'Value',
      description: "Greenblatt's Magic Formula — good businesses trading cheaply.",
      picks: value(rows),
      primary: { key: 'magic_formula_score', label: 'Magic F', type: 'num' },
      secondary: { key: 'roic', label: 'ROIC', type: 'pct' },
    },
    {
      id: 'deep_value',
      title: 'Deep Value',
      description: 'Graham-style net-nets and low-multiple contrarian picks.',
      picks: deepValue(rows),
      primary: { key: 'ncav_ratio', label: 'NCAV', type: 'num' },
      secondary: { key: 'trailing_pe', label: 'P/E', type: 'num' },
    },
  ];
}

export function unionPicks(buckets: PickBucket[]): Stock[] {
  const seen = new Set<string>();
  const out: Stock[] = [];
  for (const b of buckets) {
    for (const s of b.picks) {
      if (seen.has(s.isin)) continue;
      seen.add(s.isin);
      out.push(s);
    }
  }
  return out;
}
