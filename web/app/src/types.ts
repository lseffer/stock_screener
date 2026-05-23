export type CapTier = 'large' | 'mid' | 'small' | 'micro';

export interface Stock {
  isin: string;
  company_name: string | null;
  symbol: string | null;
  currency: string | null;
  sector: string | null;
  yahoo_ticker: string | null;
  report_date: string | null;
  market_date: string | null;
  p_score: number | null;
  p_score_1: number | null;
  p_score_2: number | null;
  p_score_3: number | null;
  p_score_4: number | null;
  p_score_5: number | null;
  p_score_6: number | null;
  p_score_7: number | null;
  p_score_8: number | null;
  p_score_9: number | null;
  roic: number | null;
  ev_ebitda_ratio_inv: number | null;
  shareholder_yield_stock: number | null;
  shareholder_yield_dividends: number | null;
  shareholder_yield_total: number | null;
  price_to_sales: number | null;
  price_to_cash_flow: number | null;
  ncav_ratio: number | null;
  price: number | null;
  target_median_price: number | null;
  number_of_analyst_opinions: number | null;
  ebitda: number | null;
  market_cap: number | null;
  market_cap_eur: number | null;
  cap_tier: CapTier | null;
  trailing_pe: number | null;
  forward_pe: number | null;
  ev_ebitda_ratio: number | null;
  magic_formula_score: number | null;
  magic_formula_score_percentile: number | null;
  roic_percentile: number | null;
  shareholder_yield_percentile: number | null;
  momentum_date: string | null;
  return_12_1: number | null;
  return_6m: number | null;
  return_3m: number | null;
  momentum_score: number | null;
  momentum_score_percentile: number | null;
  value_momentum_score: number | null;
}

export interface DataPayload {
  generated_at: string;
  rows: Stock[];
}

export type PresetId = 'top_picks' | 'overview' | 'piotroski' | 'magic' | 'value' | 'momentum' | 'all';
