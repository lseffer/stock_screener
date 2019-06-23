from sqlalchemy import Column, String, Float, Date
from .base import Base


class MagicFormulaScore(Base):
    __tablename__ = 'magic_formula_score'
    isin = Column(String, primary_key=True)
    report_date = Column(Date, primary_key=True)
    market_date = Column(Date)
    roic = Column(Float)
    ev_ebitda_ratio_inv = Column(Float)
    shareholder_yield_stock = Column(Float)
    shareholder_yield_dividends = Column(Float)
    price_to_sales = Column(Float)
    price_to_cash_flow = Column(Float)
    ncav_ratio = Column(Float)
    price = Column(Float)
    target_median_price = Column(Float)
    recommendation = Column(Float)
    number_of_analyst_opinions = Column(Float)
    ebitda = Column(Float)
    market_cap = Column(Float)
    trailing_pe = Column(Float)
    forward_pe = Column(Float)
    ev_ebitda_ratio = Column(Float)
    magic_formula_score = Column(Float)
    name = __tablename__
    sqltext = """
SELECT
    *,
    CASE
        WHEN
            SIGN(roic) = -1 AND SIGN(ev_ebitda_ratio_inv) = -1 THEN NULL
        ELSE roic * ev_ebitda_ratio_inv
    END AS magic_formula_score
FROM
    (
        SELECT
            isin,
            report_date,
            (ebit * (1-(COALESCE(income_tax_expense, 0) / NULLIF(COALESCE(income_before_tax, 0), 0)))) / NULLIF( (
            (COALESCE(total_assets, 0) - COALESCE(other_assets, 0) - COALESCE(total_current_liabilities, 0) - COALESCE
            (cash, 0)) + LAG((COALESCE(total_assets, 0) - COALESCE(other_assets, 0) - COALESCE
            (total_current_liabilities, 0) - COALESCE(cash, 0))) OVER (partition BY isin ORDER BY report_date ASC)) /
            2.0, 0) AS roic,
            1.0 / NULLIF(ev_ebitda_ratio, 0) AS ev_ebitda_ratio_inv,
            (LAG(common_stock) OVER (PARTITION BY isin ORDER BY report_date ASC) - common_stock) / NULLIF(LAG
            (common_stock) OVER (PARTITION BY isin ORDER BY report_date ASC), 0) AS shareholder_yield_stock,
            ABS(dividends_paid) / NULLIF(market_cap, 0) AS shareholder_yield_dividends,
            market_cap / NULLIF(a.total_revenue, 0) AS price_to_sales,
            market_cap / NULLIF(b.total_cash_from_operating_activities, 0) AS price_to_cash_flow,
            (COALESCE(total_current_assets, 0) - COALESCE(total_liab, 0)) / NULLIF(market_cap, 0) AS ncav_ratio,
            price,
            target_median_price,
            recommendation,
            number_of_analyst_opinions,
            ebitda,
            market_cap,
            trailing_pe,
            forward_pe,
            ev_ebitda_ratio,
            market_date
        FROM
            income_statements AS a
        FULL JOIN
            cash_flow_statements AS b
        USING
            (isin, report_date)
        FULL JOIN
            balance_sheet_statements AS c
        USING
            (isin, report_date)
        LEFT JOIN
            (
                SELECT
                    a.*
                FROM
                    prices AS a
                INNER JOIN
                    (
                        SELECT
                            isin,
                            MAX(market_date) AS market_date
                        FROM
                            prices
                        GROUP BY
                            1) AS b
                USING
                    (isin, market_date)) AS d
        USING
            (isin) ) AS a
    """
