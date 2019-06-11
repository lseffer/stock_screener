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
    p_score,
    roic,
    ev_ebitda_ratio_inv,
    shareholder_yield_stock,
    shareholder_yield_dividends,
    price_to_sales,
    price_to_cash_flow,
    ncav_ratio,
    price,
    target_median_price,
    number_of_analyst_opinions,
    ebitda,
    market_cap,
    trailing_pe,
    forward_pe,
    ev_ebitda_ratio,
    magic_formula_score
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
