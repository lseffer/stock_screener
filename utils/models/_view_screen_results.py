from sqlalchemy import Column, String, Float, Date, Integer
from .base import Base


class ScreenResults(Base):
    __tablename__ = 'screen_results'
    isin = Column(String, primary_key=True)
    company_name = Column(String)
    symbol = Column(String)
    currency = Column(String)
    sector = Column(String)
    yahoo_ticker = Column(String)
    report_date = Column(Date, primary_key=True)
    market_date = Column(Date)
    p_score = Column(Integer)
    roic = Column(Float)
    ev_ebitda_ratio_inv = Column(Float)
    shareholder_yield_stock = Column(Float)
    shareholder_yield_dividends = Column(Float)
    price_to_sales = Column(Float)
    price_to_cash_flow = Column(Float)
    ncav_ratio = Column(Float)
    price = Column(Float)
    target_median_price = Column(Float)
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
    isin,
    name AS company_name,
    symbol,
    currency,
    sector,
    yahoo_ticker,
    report_date,
    market_date,
    CASE
        WHEN p_score IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            p_score
        END AS p_score,
    CASE
        WHEN roic IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            roic
        END AS roic,
    CASE
        WHEN ev_ebitda_ratio_inv IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            ev_ebitda_ratio_inv
        END AS ev_ebitda_ratio_inv,
    CASE
        WHEN shareholder_yield_stock IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            shareholder_yield_stock
        END AS shareholder_yield_stock,
    CASE
        WHEN shareholder_yield_dividends IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            shareholder_yield_dividends
        END AS shareholder_yield_dividends,
    CASE
        WHEN price_to_sales IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            price_to_sales
        END AS price_to_sales,
    CASE
        WHEN price_to_cash_flow IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            price_to_cash_flow
        END AS price_to_cash_flow,
    CASE
        WHEN ncav_ratio IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            ncav_ratio
        END AS ncav_ratio,
    CASE
        WHEN price IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            price
        END AS price,
    CASE
        WHEN target_median_price IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            target_median_price
        END AS target_median_price,
    CASE
        WHEN number_of_analyst_opinions IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            number_of_analyst_opinions
        END AS number_of_analyst_opinions,
    CASE
        WHEN ebitda IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            ebitda
        END AS ebitda,
    CASE
        WHEN market_cap IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            market_cap
        END AS market_cap,
    CASE
        WHEN trailing_pe IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            trailing_pe
        END AS trailing_pe,
    CASE
        WHEN forward_pe IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            forward_pe
        END AS forward_pe,
    CASE
        WHEN ev_ebitda_ratio IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            ev_ebitda_ratio
        END AS ev_ebitda_ratio,
    CASE
        WHEN magic_formula_score IN ('Infinity'::Float, -'Infinity'::Float) THEN
            NULL
        ELSE
            magic_formula_score
        END AS magic_formula_score
FROM
    piotroski_score AS a
FULL JOIN
    magic_formula_score AS b
USING
    (isin, report_date)
LEFT JOIN
    stocks AS c
USING
    (isin)
    """
