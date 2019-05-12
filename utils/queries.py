from utils.models import Stock, IncomeStatement, BalanceSheetStatement, CashFlowStatement, PiotroskiScore
from typing import List, Tuple, Union, Dict
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
    )).group_by(Stock.isin, Stock.yahoo_ticker).all()
    return res


def screened_stocks() -> List[Dict]:
    session = Session()
    res: List[Tuple] = session.query(PiotroskiScore)\
        .filter(func.extract('year', PiotroskiScore.report_date) == get_last_year().year).all()
    res1 = [row.__json__() for row in res]
    return res1
