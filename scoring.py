"""
Compute Piotroski F-Score and Magic Formula screening scores in Python,
replacing the PostgreSQL materialized views.
"""
import sqlite3
import polars as pl
from utils.config import DB_PATH, get_logger
from utils.fx import EUR_RATES

logger = get_logger('scoring')


def _get_conn():
    return sqlite3.connect(DB_PATH)


def _read_table(query: str, conn, table_name: str) -> pl.DataFrame:
    """Read from SQLite with explicit Float64 overrides for REAL columns.
    SQLite's dynamic typing stores round floats as integers, causing polars
    schema inference to fail on mixed int/float columns."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    schema_overrides = {
        row[1]: pl.Float64 for row in cursor.fetchall()
        if row[2].upper() in ('REAL', 'FLOAT')
    }
    return pl.read_database(query, conn, schema_overrides=schema_overrides)


def _safe_div(a: pl.Expr, b: pl.Expr) -> pl.Expr:
    """Safe division returning null for zero/null divisors and infinite results."""
    result = a / b
    return pl.when(result.is_infinite() | result.is_nan()).then(None).otherwise(result)


def load_financial_data() -> pl.DataFrame:
    """Load and join all financial tables into a single DataFrame."""
    conn = _get_conn()
    income = _read_table('SELECT * FROM income_statements', conn, 'income_statements')
    balance = _read_table('SELECT * FROM balance_sheet_statements', conn, 'balance_sheet_statements')
    cashflow = _read_table('SELECT * FROM cash_flow_statements', conn, 'cash_flow_statements')
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
    prices = _read_table('''
        SELECT a.* FROM prices a
        INNER JOIN (SELECT isin, MAX(market_date) AS market_date FROM prices GROUP BY isin) b
        ON a.isin = b.isin AND a.market_date = b.market_date
    ''', conn, 'prices')
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

    n_companies = fin_data['isin'].n_unique()
    logger.info('Loaded %s rows across %s companies', len(fin_data), n_companies)

    logger.info('Computing Piotroski scores...')
    piotroski = compute_piotroski_scores(fin_data)

    logger.info('Computing Magic Formula scores...')
    magic = compute_magic_formula_scores(fin_data)

    scores = piotroski.join(magic, on=['isin', 'report_date'], how='full', coalesce=True)

    conn = _get_conn()
    stocks = _read_table('SELECT isin, name, symbol, currency, sector, yahoo_ticker FROM stocks', conn, 'stocks')
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

    results = _add_market_cap_eur(results)
    results = _add_cap_tier(results)
    results = _add_shareholder_yield_total(results)
    results = _add_percentile_ranks(results)

    output_cols = [
        'isin', 'company_name', 'symbol', 'currency', 'sector', 'yahoo_ticker',
        'report_date', 'market_date', 'p_score',
        'roic', 'ev_ebitda_ratio_inv', 'shareholder_yield_stock',
        'shareholder_yield_dividends', 'shareholder_yield_total',
        'price_to_sales', 'price_to_cash_flow',
        'ncav_ratio', 'price', 'target_median_price',
        'number_of_analyst_opinions', 'ebitda', 'market_cap',
        'market_cap_eur', 'cap_tier',
        'trailing_pe', 'forward_pe', 'ev_ebitda_ratio', 'magic_formula_score',
        'magic_formula_score_percentile', 'roic_percentile',
        'shareholder_yield_percentile',
    ]
    existing_output_cols = [c for c in output_cols if c in results.columns]
    results = results.select(existing_output_cols)

    logger.info(
        'Computed screen results: %s rows across %s companies',
        len(results), results['isin'].n_unique(),
    )
    return results


def _add_market_cap_eur(df: pl.DataFrame) -> pl.DataFrame:
    """Add ``market_cap_eur`` by multiplying ``market_cap`` by the FX rate for the row's currency."""
    if 'market_cap' not in df.columns or 'currency' not in df.columns:
        return df
    return df.with_columns(
        (pl.col('market_cap') * pl.col('currency').str.to_uppercase().replace_strict(
            EUR_RATES, default=None, return_dtype=pl.Float64
        )).alias('market_cap_eur')
    )


# Nordic-scaled cap-tier thresholds, in EUR.
_CAP_TIER_LARGE = 5_000_000_000
_CAP_TIER_MID = 1_000_000_000
_CAP_TIER_SMALL = 150_000_000


def _add_cap_tier(df: pl.DataFrame) -> pl.DataFrame:
    if 'market_cap_eur' not in df.columns:
        return df
    return df.with_columns(
        pl.when(pl.col('market_cap_eur').is_null()).then(None)
        .when(pl.col('market_cap_eur') >= _CAP_TIER_LARGE).then(pl.lit('large'))
        .when(pl.col('market_cap_eur') >= _CAP_TIER_MID).then(pl.lit('mid'))
        .when(pl.col('market_cap_eur') >= _CAP_TIER_SMALL).then(pl.lit('small'))
        .otherwise(pl.lit('micro'))
        .alias('cap_tier')
    )


def _add_shareholder_yield_total(df: pl.DataFrame) -> pl.DataFrame:
    """Combined shareholder yield = buyback yield + dividend yield. Null when both sources are null."""
    if 'shareholder_yield_stock' not in df.columns or 'shareholder_yield_dividends' not in df.columns:
        return df
    return df.with_columns(
        pl.when(
            pl.col('shareholder_yield_stock').is_null()
            & pl.col('shareholder_yield_dividends').is_null()
        )
        .then(None)
        .otherwise(
            pl.col('shareholder_yield_stock').fill_null(0)
            + pl.col('shareholder_yield_dividends').fill_null(0)
        )
        .alias('shareholder_yield_total')
    )


def _percentile_expr(col: str) -> pl.Expr:
    """Ascending percentile (0-100) where higher value = higher percentile.

    Nulls stay null. Ties get the average rank. Result is divided by the
    count of non-null values so the top value sits at ~100.
    """
    non_null_count = pl.col(col).is_not_null().sum()
    ranks = pl.col(col).rank(method='average')
    return (
        pl.when(pl.col(col).is_null())
        .then(None)
        .otherwise((ranks / non_null_count) * 100.0)
        .alias(f'{col}_percentile')
    )


def _add_percentile_ranks(df: pl.DataFrame) -> pl.DataFrame:
    exprs = []
    for col in ('magic_formula_score', 'roic', 'shareholder_yield_total'):
        if col in df.columns:
            exprs.append(_percentile_expr(col))
    # shareholder_yield_total_percentile -> shareholder_yield_percentile for brevity
    df = df.with_columns(exprs) if exprs else df
    if 'shareholder_yield_total_percentile' in df.columns:
        df = df.rename({'shareholder_yield_total_percentile': 'shareholder_yield_percentile'})
    return df
