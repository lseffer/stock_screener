from utils.models import Stock
from typing import List, Tuple
from utils.config import Session


def fetch_all_tickers_from_database() -> List[Tuple]:
    session = Session()
    res: List[Tuple] = session.query(Stock.isin, Stock.yahoo_ticker).group_by(Stock.isin, Stock.yahoo_ticker).all()
    session.close()
    return res
