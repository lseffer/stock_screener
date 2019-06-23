from utils import fetch_yahoo_data
from utils.queries import fetch_all_tickers_from_database
from utils.models import Base, Price
from utils.config import logger
from utils.etl_base import ETLBase
from typing import List


def create_database_records() -> List[Base]:
    tickers = fetch_all_tickers_from_database()
    data: List[Base] = []
    for ticker_tuple in tickers:
        if len(ticker_tuple) == 2:
            try:
                response = fetch_yahoo_data(ticker_tuple[1], 'summaryDetail,financialData,price,defaultKeyStatistics')
                record = Price.process_response(response, ticker_tuple[0])
            except Exception:
                logger.error('Something went wrong getting ticker %s' % ticker_tuple[1])
                continue
            data.append(record)
        else:
            continue
    return data


class StockValuationETL(ETLBase):

    @staticmethod
    def job() -> None:
        data = create_database_records()
        ETLBase.load_data(data)
