from utils.models import Stock, IncomeStatement, BalanceSheetStatement, CashFlowStatement
from typing import List, Tuple, Union
from utils.config import Session, get_last_year
from sqlalchemy import func


def fetch_all_tickers_from_database() -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).group_by(Stock.isin, Stock.yahoo_ticker).all()
    session.close()
    return res


def fetch_isins_not_updated_financials(Model: Union[IncomeStatement,
                                                    BalanceSheetStatement,
                                                    CashFlowStatement]) -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).filter(~Stock.isin.in_(
        session.query(Model.isin).filter(func.extract('year', Model.report_date) == get_last_year().year).all()
    )).all()
    return res
