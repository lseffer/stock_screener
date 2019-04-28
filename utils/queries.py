from utils.models import Stock, IncomeStatement, BalanceSheetStatement, CashFlowStatement
from typing import List, Tuple, Union
from utils.config import Session, LAST_YEAR
from sqlalchemy import func


def fetch_all_tickers_from_database() -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).group_by(Stock.isin, Stock.yahoo_ticker).all()
    session.close()
    return res


def fetch_isins_without_updated_financial_statements(Model: Union[IncomeStatement,
                                                                  BalanceSheetStatement,
                                                                  CashFlowStatement]) -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).filter(~Stock.isin.in_(
        session.query(Model.isin).filter(func.extract('year', Model.report_date) == LAST_YEAR.year).all()
    )).all()
    return res
