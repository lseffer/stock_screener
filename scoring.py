"""
Compute Piotroski F-Score and Magic Formula screening scores in Python,
replacing the PostgreSQL materialized views.
"""
import pandas as pd
import math
from utils.config import engine, logger


def _safe_div(a, b):
    """Safe division returning None for zero/None divisors."""
    if a is None or b is None or b == 0:
        return None
    result = a / b
    if math.isinf(result) or math.isnan(result):
        return None
    return result


def _sanitize_float(val):
    """Replace inf/nan with None."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isinf(val) or math.isnan(val)):
        return None
    return val


def load_financial_data() -> pd.DataFrame:
    """Load and join all financial tables into a single DataFrame."""
    income = pd.read_sql('SELECT * FROM income_statements', engine)
    balance = pd.read_sql('SELECT * FROM balance_sheet_statements', engine)
    cashflow = pd.read_sql('SELECT * FROM cash_flow_statements', engine)

    # Merge on isin + report_date
    df = income.merge(cashflow, on=['isin', 'report_date'], how='outer', suffixes=('', '_cf'))
    df = df.merge(balance, on=['isin', 'report_date'], how='outer', suffixes=('', '_bs'))

    # Use cashflow net_income if income statement one is missing
    if 'net_income_cf' in df.columns:
        df['net_income'] = df['net_income'].fillna(df['net_income_cf'])

    df = df.sort_values(['isin', 'report_date']).reset_index(drop=True)
    return df


def compute_piotroski_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Piotroski F-Score (9 financial health metrics)."""
    # Derived metrics
    df['return_on_assets'] = df.apply(
        lambda r: _safe_div(r.get('net_income'), r.get('total_assets')), axis=1)
    df['gross_margin_pct'] = df.apply(
        lambda r: _safe_div(
            (r.get('total_revenue') or 0) - (r.get('cost_of_revenue') or 0),
            r.get('total_revenue')), axis=1)
    df['current_ratio'] = df.apply(
        lambda r: _safe_div(r.get('total_current_assets'), r.get('total_current_liabilities')), axis=1)
    df['net_shares_issued'] = df.apply(
        lambda r: (r.get('issuance_of_stock') or 0) + (r.get('repurchase_of_stock') or 0), axis=1)

    # Compute asset turnover: revenue / avg(total_assets)
    df['prev_total_assets'] = df.groupby('isin')['total_assets'].shift(1)
    df['avg_total_assets'] = df.apply(
        lambda r: ((r.get('prev_total_assets') or r.get('total_assets') or 0) +
                   (r.get('total_assets') or 0)) / 2
        if r.get('total_assets') else None, axis=1)
    df['asset_turnover'] = df.apply(
        lambda r: _safe_div(r.get('total_revenue'), r.get('avg_total_assets')), axis=1)

    # Lag values for year-over-year comparisons
    df['prev_roa'] = df.groupby('isin')['return_on_assets'].shift(1)
    df['prev_current_ratio'] = df.groupby('isin')['current_ratio'].shift(1)
    df['prev_long_term_debt'] = df.groupby('isin')['long_term_debt'].shift(1)
    df['prev_gross_margin'] = df.groupby('isin')['gross_margin_pct'].shift(1)
    df['prev_asset_turnover'] = df.groupby('isin')['asset_turnover'].shift(1)

    # 9 Piotroski criteria
    df['p_score_1'] = (df['return_on_assets'].fillna(0) > 0).astype(int)
    df['p_score_2'] = (df['total_cash_from_operating_activities'].fillna(0) > 0).astype(int)
    df['p_score_3'] = df.apply(
        lambda r: 1 if r.get('return_on_assets') is not None and r.get('prev_roa') is not None
        and r['return_on_assets'] > r['prev_roa'] else 0, axis=1)
    df['p_score_4'] = df.apply(
        lambda r: 1 if r.get('total_cash_from_operating_activities') is not None
        and r.get('net_income') is not None
        and r['total_cash_from_operating_activities'] > r['net_income'] else 0, axis=1)
    df['p_score_5'] = df.apply(
        lambda r: 1 if r.get('long_term_debt') is not None and r.get('prev_long_term_debt') is not None
        and r['long_term_debt'] < r['prev_long_term_debt'] else 0, axis=1)
    df['p_score_6'] = df.apply(
        lambda r: 1 if r.get('current_ratio') is not None and r.get('prev_current_ratio') is not None
        and r['current_ratio'] > r['prev_current_ratio'] else 0, axis=1)
    df['p_score_7'] = (df['net_shares_issued'].fillna(0) <= 0).astype(int)
    df['p_score_8'] = df.apply(
        lambda r: 1 if r.get('gross_margin_pct') is not None and r.get('prev_gross_margin') is not None
        and r['gross_margin_pct'] > r['prev_gross_margin'] else 0, axis=1)
    df['p_score_9'] = df.apply(
        lambda r: 1 if r.get('asset_turnover') is not None and r.get('prev_asset_turnover') is not None
        and r['asset_turnover'] > r['prev_asset_turnover'] else 0, axis=1)

    df['p_score'] = sum(df[f'p_score_{i}'] for i in range(1, 10))

    return df[['isin', 'report_date', 'p_score_1', 'p_score_2', 'p_score_3',
               'p_score_4', 'p_score_5', 'p_score_6', 'p_score_7', 'p_score_8',
               'p_score_9', 'p_score']]


def compute_magic_formula_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Magic Formula and valuation metrics."""
    # Load latest prices per stock
    prices = pd.read_sql('''
        SELECT a.* FROM prices a
        INNER JOIN (SELECT isin, MAX(market_date) AS market_date FROM prices GROUP BY isin) b
        ON a.isin = b.isin AND a.market_date = b.market_date
    ''', engine)

    # Merge prices with financial data
    merged = df.merge(prices, on='isin', how='left', suffixes=('', '_price'))

    # ROIC: NOPAT / avg invested capital
    merged['tax_rate'] = merged.apply(
        lambda r: _safe_div(r.get('income_tax_expense') or 0, r.get('income_before_tax') or 0), axis=1)
    merged['nopat'] = merged.apply(
        lambda r: (r.get('ebit') or 0) * (1 - (r.get('tax_rate') or 0))
        if r.get('ebit') is not None else None, axis=1)
    merged['invested_capital'] = merged.apply(
        lambda r: (r.get('total_assets') or 0) - (r.get('other_assets') or 0)
        - (r.get('total_current_liabilities') or 0) - (r.get('cash') or 0), axis=1)
    merged['prev_invested_capital'] = merged.groupby('isin')['invested_capital'].shift(1)
    merged['avg_invested_capital'] = merged.apply(
        lambda r: ((r.get('invested_capital') or 0) + (r.get('prev_invested_capital') or r.get('invested_capital') or 0)) / 2,
        axis=1)
    merged['roic'] = merged.apply(
        lambda r: _safe_div(r.get('nopat'), r.get('avg_invested_capital')), axis=1)

    # EV/EBITDA inverse
    merged['ev_ebitda_ratio_inv'] = merged.apply(
        lambda r: _safe_div(1.0, r.get('ev_ebitda_ratio')), axis=1)

    # Shareholder yield
    merged['prev_common_stock'] = merged.groupby('isin')['common_stock'].shift(1)
    merged['shareholder_yield_stock'] = merged.apply(
        lambda r: _safe_div(
            (r.get('prev_common_stock') or 0) - (r.get('common_stock') or 0),
            r.get('prev_common_stock')) if r.get('prev_common_stock') else None, axis=1)
    merged['shareholder_yield_dividends'] = merged.apply(
        lambda r: _safe_div(abs(r.get('dividends_paid') or 0), r.get('market_cap')), axis=1)

    # Valuation ratios
    merged['price_to_sales'] = merged.apply(
        lambda r: _safe_div(r.get('market_cap'), r.get('total_revenue')), axis=1)
    merged['price_to_cash_flow'] = merged.apply(
        lambda r: _safe_div(r.get('market_cap'), r.get('total_cash_from_operating_activities')), axis=1)
    merged['ncav_ratio'] = merged.apply(
        lambda r: _safe_div(
            (r.get('total_current_assets') or 0) - (r.get('total_liab') or 0),
            r.get('market_cap')), axis=1)

    # Magic formula composite score
    merged['magic_formula_score'] = merged.apply(
        lambda r: r.get('roic', 0) * r.get('ev_ebitda_ratio_inv', 0)
        if r.get('roic') is not None and r.get('ev_ebitda_ratio_inv') is not None
        and not (r.get('roic', 0) < 0 and r.get('ev_ebitda_ratio_inv', 0) < 0)
        else None, axis=1)

    result_cols = ['isin', 'report_date', 'market_date', 'roic', 'ev_ebitda_ratio_inv',
                   'shareholder_yield_stock', 'shareholder_yield_dividends',
                   'price_to_sales', 'price_to_cash_flow', 'ncav_ratio',
                   'price', 'target_median_price', 'recommendation',
                   'number_of_analyst_opinions', 'ebitda_price', 'market_cap',
                   'trailing_pe', 'forward_pe', 'ev_ebitda_ratio', 'magic_formula_score']

    # Rename ebitda_price back to ebitda (it came from prices table merge)
    existing_cols = [c for c in result_cols if c in merged.columns]
    result = merged[existing_cols].copy()
    if 'ebitda_price' in result.columns:
        result = result.rename(columns={'ebitda_price': 'ebitda'})

    return result


def compute_screen_results() -> pd.DataFrame:
    """Compute final screening results joining Piotroski and Magic Formula scores with stock info."""
    logger.info('Loading financial data...')
    fin_data = load_financial_data()

    if fin_data.empty:
        logger.warning('No financial data available')
        return pd.DataFrame()

    logger.info('Computing Piotroski scores...')
    piotroski = compute_piotroski_scores(fin_data)

    logger.info('Computing Magic Formula scores...')
    magic = compute_magic_formula_scores(fin_data)

    # Join Piotroski and Magic Formula
    scores = piotroski.merge(magic, on=['isin', 'report_date'], how='outer')

    # Join with stock info
    stocks = pd.read_sql('SELECT isin, name, symbol, currency, sector, yahoo_ticker FROM stocks', engine)
    results = scores.merge(stocks, on='isin', how='left')

    # Rename for output
    results = results.rename(columns={'name': 'company_name'})

    # Sanitize infinity/nan values
    float_cols = results.select_dtypes(include=['float64', 'float32']).columns
    for col in float_cols:
        results[col] = results[col].apply(_sanitize_float)

    # Select and order final columns
    output_cols = [
        'isin', 'company_name', 'symbol', 'currency', 'sector', 'yahoo_ticker',
        'report_date', 'market_date', 'p_score',
        'roic', 'ev_ebitda_ratio_inv', 'shareholder_yield_stock',
        'shareholder_yield_dividends', 'price_to_sales', 'price_to_cash_flow',
        'ncav_ratio', 'price', 'target_median_price',
        'number_of_analyst_opinions', 'ebitda', 'market_cap',
        'trailing_pe', 'forward_pe', 'ev_ebitda_ratio', 'magic_formula_score'
    ]
    existing_output_cols = [c for c in output_cols if c in results.columns]
    results = results[existing_output_cols]

    logger.info('Computed screen results for %s stock-periods' % len(results))
    return results
