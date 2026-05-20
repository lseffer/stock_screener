from datetime import date, timedelta
from typing import List, Tuple, Union

from sqlalchemy import func, Integer, cast

from utils.config import Session, get_last_year
from utils.models import (
    BalanceSheetStatement,
    CashFlowStatement,
    IncomeStatement,
    Price,
    Stock,
)


def fetch_all_tickers_from_database() -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).group_by(Stock.isin, Stock.yahoo_ticker).all()
    session.close()
    return res


def fetch_tickers_needing_price_update(max_age_days: int = 5) -> List[Tuple]:
    """Return tickers that don't have a price record within the last max_age_days."""
    session = Session()
    cutoff = date.today() - timedelta(days=max_age_days)
    recently_updated = (
        session.query(Price.isin)
        .filter(Price.market_date >= cutoff)
        .subquery()
    )
    res: List[Tuple] = (
        session.query(Stock.isin, Stock.yahoo_ticker)
        .filter(~Stock.isin.in_(session.query(recently_updated.c.isin)))
        .group_by(Stock.isin, Stock.yahoo_ticker)
        .all()
    )
    session.close()
    return res


def fetch_tickers_needing_financials(
    Model: Union[type[IncomeStatement], type[BalanceSheetStatement], type[CashFlowStatement]],
) -> List[Tuple]:
    """Return tickers that don't have financial statement data for the last fiscal year."""
    session = Session()
    last_year = get_last_year().year
    has_current_data = (
        session.query(Model.isin)
        .filter(cast(func.strftime('%Y', Model.report_date), Integer) == last_year)  # type: ignore
        .subquery()
    )
    res: List[Tuple] = (
        session.query(Stock.isin, Stock.yahoo_ticker)
        .filter(~Stock.isin.in_(session.query(has_current_data.c.isin)))
        .group_by(Stock.isin, Stock.yahoo_ticker)
        .all()
    )
    session.close()
    return res
