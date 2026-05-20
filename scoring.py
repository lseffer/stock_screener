"""
Compute Piotroski F-Score and Magic Formula screening scores in Python,
replacing the PostgreSQL materialized views.
"""
import sqlite3
import polars as pl
from utils.config import DB_PATH, logger


def _get_conn():
    return sqlite3.connect(DB_PATH)


def _safe_div(a: pl.Expr, b: pl.Expr) -> pl.Expr:
    """Safe division returning null for zero/null divisors and infinite results."""
    result = a / b
    return pl.when(result.is_infinite() | result.is_nan()).then(None).otherwise(result)


def load_financial_data() -> pl.DataFrame:
    """Load and join all financial tables into a single DataFrame."""
    conn = _get_conn()
    income = pl.read_database('SELECT * FROM income_statements', conn)
    balance = pl.read_database('SELECT * FROM balance_sheet_statements', conn)
    cashflow = pl.read_database('SELECT * FROM cash_flow_statements', conn)
    conn.close()

    df = income.join(cashflow, on=['isin', 'report_date'], how='full', suffix='_cf', coalesce=True)
    df = df.join(balance, on=['isin', 'report_date'], how='full', suffix='_bs', coalesce=True)

    if 'net_income_cf' in df.columns:
        df = df.with_columns(
            pl.col('net_income').fill_null(pl.col('net_income_cf')).alias('net_income')
        )

    df = df.sort(['isin', 'report_date'])
    return df


def compute_piotroski_scores(df: pl.DataFrame) -> pl.DataFrame:
    """Compute Piotroski F-Score (9 financial health metrics)."""
    df = df.with_columns([
        _safe_div(pl.col('net_income'), pl.col('total_assets')).alias('return_on_assets'),
        _safe_div(
            pl.col('total_revenue').fill_null(0) - pl.col('cost_of_revenue').fill_null(0),
            pl.col('total_revenue')
        ).alias('gross_margin_pct'),
        _safe_div(
            pl.col('total_current_assets'), pl.col('total_current_liabilities')
        ).alias('current_ratio'),
        (pl.col('issuance_of_stock').fill_null(0) + pl.col('repurchase_of_stock').fill_null(0))
        .alias('net_shares_issued'),
    ])

    df = df.with_columns(
        pl.col('total_assets').shift(1).over('isin').alias('prev_total_assets')
    )
    df = df.with_columns(
        pl.when(pl.col('total_assets').is_not_null())
        .then(
            (pl.col('prev_total_assets').fill_null(pl.col('total_assets')).fill_null(0)
             + pl.col('total_assets').fill_null(0)) / 2
        )
        .otherwise(None)
        .alias('avg_total_assets')
    )
    df = df.with_columns(
        _safe_div(pl.col('total_revenue'), pl.col('avg_total_assets')).alias('asset_turnover')
    )

    df = df.with_columns([
        pl.col('return_on_assets').shift(1).over('isin').alias('prev_roa'),
        pl.col('current_ratio').shift(1).over('isin').alias('prev_current_ratio'),
        pl.col('long_term_debt').shift(1).over('isin').alias('prev_long_term_debt'),
        pl.col('gross_margin_pct').shift(1).over('isin').alias('prev_gross_margin'),
        pl.col('asset_turnover').shift(1).over('isin').alias('prev_asset_turnover'),
    ])

    df = df.with_columns([
        (pl.col('return_on_assets').fill_null(0) > 0).cast(pl.Int64).alias('p_score_1'),
        (pl.col('total_cash_from_operating_activities').fill_null(0) > 0).cast(pl.Int64).alias('p_score_2'),
        pl.when(
            pl.col('return_on_assets').is_not_null()
            & pl.col('prev_roa').is_not_null()
            & (pl.col('return_on_assets') > pl.col('prev_roa'))
        ).then(1).otherwise(0).alias('p_score_3'),
        pl.when(
            pl.col('total_cash_from_operating_activities').is_not_null()
            & pl.col('net_income').is_not_null()
            & (pl.col('total_cash_from_operating_activities') > pl.col('net_income'))
        ).then(1).otherwise(0).alias('p_score_4'),
        pl.when(
            pl.col('long_term_debt').is_not_null()
            & pl.col('prev_long_term_debt').is_not_null()
            & (pl.col('long_term_debt') < pl.col('prev_long_term_debt'))
        ).then(1).otherwise(0).alias('p_score_5'),
        pl.when(
            pl.col('current_ratio').is_not_null()
            & pl.col('prev_current_ratio').is_not_null()
            & (pl.col('current_ratio') > pl.col('prev_current_ratio'))
        ).then(1).otherwise(0).alias('p_score_6'),
        (pl.col('net_shares_issued').fill_null(0) <= 0).cast(pl.Int64).alias('p_score_7'),
        pl.when(
            pl.col('gross_margin_pct').is_not_null()
            & pl.col('prev_gross_margin').is_not_null()
            & (pl.col('gross_margin_pct') > pl.col('prev_gross_margin'))
        ).then(1).otherwise(0).alias('p_score_8'),
        pl.when(
            pl.col('asset_turnover').is_not_null()
            & pl.col('prev_asset_turnover').is_not_null()
            & (pl.col('asset_turnover') > pl.col('prev_asset_turnover'))
        ).then(1).otherwise(0).alias('p_score_9'),
    ])

    df = df.with_columns(
        pl.sum_horizontal(pl.col(f'p_score_{i}') for i in range(1, 10)).alias('p_score')
    )

    return df.select(
        ['isin', 'report_date'] + [f'p_score_{i}' for i in range(1, 10)] + ['p_score']
    )


def compute_magic_formula_scores(df: pl.DataFrame) -> pl.DataFrame:
    """Compute Magic Formula and valuation metrics."""
    conn = _get_conn()
    prices = pl.read_database('''
        SELECT a.* FROM prices a
        INNER JOIN (SELECT isin, MAX(market_date) AS market_date FROM prices GROUP BY isin) b
        ON a.isin = b.isin AND a.market_date = b.market_date
    ''', conn)
    conn.close()

    merged = df.join(prices, on='isin', how='left', suffix='_price')

    # ROIC: NOPAT / avg invested capital
    merged = merged.with_columns(
        _safe_div(
            pl.col('income_tax_expense').fill_null(0),
            pl.col('income_before_tax').fill_null(0)
        ).alias('tax_rate')
    )
    merged = merged.with_columns(
        pl.when(pl.col('ebit').is_not_null())
        .then(pl.col('ebit').fill_null(0) * (1 - pl.col('tax_rate').fill_null(0)))
        .otherwise(None)
        .alias('nopat')
    )
    merged = merged.with_columns(
        (pl.col('total_assets').fill_null(0) - pl.col('other_assets').fill_null(0)
         - pl.col('total_current_liabilities').fill_null(0) - pl.col('cash').fill_null(0))
        .alias('invested_capital')
    )
    merged = merged.with_columns(
        pl.col('invested_capital').shift(1).over('isin').alias('prev_invested_capital')
    )
    merged = merged.with_columns(
        ((pl.col('invested_capital').fill_null(0)
          + pl.col('prev_invested_capital').fill_null(pl.col('invested_capital')).fill_null(0)) / 2)
        .alias('avg_invested_capital')
    )
    merged = merged.with_columns(
        _safe_div(pl.col('nopat'), pl.col('avg_invested_capital')).alias('roic')
    )

    # EV/EBITDA inverse
    merged = merged.with_columns(
        _safe_div(pl.lit(1.0), pl.col('ev_ebitda_ratio')).alias('ev_ebitda_ratio_inv')
    )

    # Shareholder yield
    merged = merged.with_columns(
        pl.col('common_stock').shift(1).over('isin').alias('prev_common_stock')
    )
    merged = merged.with_columns([
        pl.when(pl.col('prev_common_stock').is_not_null())
        .then(_safe_div(
            pl.col('prev_common_stock').fill_null(0) - pl.col('common_stock').fill_null(0),
            pl.col('prev_common_stock')
        ))
        .otherwise(None)
        .alias('shareholder_yield_stock'),
        _safe_div(
            pl.col('dividends_paid').fill_null(0).abs(),
            pl.col('market_cap')
        ).alias('shareholder_yield_dividends'),
    ])

    # Valuation ratios
    merged = merged.with_columns([
        _safe_div(pl.col('market_cap'), pl.col('total_revenue')).alias('price_to_sales'),
        _safe_div(
            pl.col('market_cap'), pl.col('total_cash_from_operating_activities')
        ).alias('price_to_cash_flow'),
        _safe_div(
            pl.col('total_current_assets').fill_null(0) - pl.col('total_liab').fill_null(0),
            pl.col('market_cap')
        ).alias('ncav_ratio'),
    ])

    # Magic formula composite score (exclude case where both ROIC and EV/EBITDA inverse are negative)
    merged = merged.with_columns(
        pl.when(
            pl.col('roic').is_not_null()
            & pl.col('ev_ebitda_ratio_inv').is_not_null()
            & ~((pl.col('roic') < 0) & (pl.col('ev_ebitda_ratio_inv') < 0))
        )
        .then(pl.col('roic') * pl.col('ev_ebitda_ratio_inv'))
        .otherwise(None)
        .alias('magic_formula_score')
    )

    result_cols = ['isin', 'report_date', 'market_date', 'roic', 'ev_ebitda_ratio_inv',
                   'shareholder_yield_stock', 'shareholder_yield_dividends',
                   'price_to_sales', 'price_to_cash_flow', 'ncav_ratio',
                   'price', 'target_median_price', 'recommendation',
                   'number_of_analyst_opinions', 'ebitda', 'market_cap',
                   'trailing_pe', 'forward_pe', 'ev_ebitda_ratio', 'magic_formula_score']

    existing_cols = [c for c in result_cols if c in merged.columns]
    return merged.select(existing_cols)


def compute_screen_results() -> pl.DataFrame:
    """Compute final screening results joining Piotroski and Magic Formula scores with stock info."""
    logger.info('Loading financial data...')
    fin_data = load_financial_data()

    if fin_data.is_empty():
        logger.warning('No financial data available')
        return pl.DataFrame()

    logger.info('Computing Piotroski scores...')
    piotroski = compute_piotroski_scores(fin_data)

    logger.info('Computing Magic Formula scores...')
    magic = compute_magic_formula_scores(fin_data)

    scores = piotroski.join(magic, on=['isin', 'report_date'], how='full', coalesce=True)

    conn = _get_conn()
    stocks = pl.read_database('SELECT isin, name, symbol, currency, sector, yahoo_ticker FROM stocks', conn)
    conn.close()
    results = scores.join(stocks, on='isin', how='left')

    results = results.rename({'name': 'company_name'})

    # Sanitize infinity/nan values in float columns
    float_cols = [c for c, dtype in results.schema.items() if dtype in (pl.Float32, pl.Float64)]
    if float_cols:
        results = results.with_columns([
            pl.when(pl.col(c).is_infinite() | pl.col(c).is_nan())
            .then(None)
            .otherwise(pl.col(c))
            .alias(c)
            for c in float_cols
        ])

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
    results = results.select(existing_output_cols)

    logger.info('Computed screen results for %s stock-periods' % len(results))
    return results
