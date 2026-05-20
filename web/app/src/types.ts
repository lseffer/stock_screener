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
  roic: number | null;
  ev_ebitda_ratio_inv: number | null;
  shareholder_yield_stock: number | null;
  shareholder_yield_dividends: number | null;
  price_to_sales: number | null;
  price_to_cash_flow: number | null;
  ncav_ratio: number | null;
  price: number | null;
  target_median_price: number | null;
  number_of_analyst_opinions: number | null;
  ebitda: number | null;
  market_cap: number | null;
  trailing_pe: number | null;
  forward_pe: number | null;
  ev_ebitda_ratio: number | null;
  magic_formula_score: number | null;
}

export interface DataPayload {
  generated_at: string;
  rows: Stock[];
}

export type PresetId = 'top_picks' | 'overview' | 'piotroski' | 'magic' | 'value' | 'all';
