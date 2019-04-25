import requests
from utils.models import Stock, Price
from utils.config import Session, logger
from utils.etl_base import ETLBase
from datetime import datetime

YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}"


def get_nested(dict_, *keys, default=None):
    # Recursive helper function for traversing nested dictionaries
    if not isinstance(dict_, dict):
        return default
    elem = dict_.get(keys[0], default)
    if len(keys) == 1:
        return elem
    return get_nested(elem, *keys[1:], default=default)


def get_all_yahoo_tickers():
    session = Session()
    res = session.query(Stock.isin, Stock.yahoo_ticker).group_by(Stock.isin, Stock.yahoo_ticker).all()
    session.close()
    # Remember this is a list of tuples
    return res


def get_yahoo_data(isin, yahoo_ticker):
    params = {"formatted": "false",
              "lang": "en-US",
              "region": "US",
              "modules": "summaryDetail,financialData,defaultKeyStatistics,price",
              "corsDomain": "finance.yahoo.com"}
    response = requests.get(YAHOO_FINANCE_BASE_URL.format(yahoo_ticker), params=params).json()
    response = get_nested(response, 'quoteSummary', 'result')[0]
    record = {
        'isin': isin,
        'market_date': datetime.fromtimestamp(get_nested(response, 'price', 'regularMarketTime')).date(),
        'price': get_nested(response, 'financialData', 'currentPrice', 'raw'),
        'target_median_price': get_nested(response, 'financialData', 'targetMedianPrice', 'raw'),
        'recommendation': get_nested(response, 'financialData', 'recommendationKey', 'raw'),
        'number_of_analyst_opinions': get_nested(response, 'financialData', 'numberOfAnalystOpinions', 'raw'),
        'ebitda': get_nested(response, 'financialData', 'ebitda', 'raw'),
        'market_cap': get_nested(response, 'summaryDetail', 'marketCap', 'raw'),
        'trailing_pe': get_nested(response, 'summaryDetail', 'trailingPE', 'raw'),
        'forward_pe': get_nested(response, 'summaryDetail', 'forwardPE', 'raw'),
        'ev_ebitda_ratio': get_nested(response, 'defaultKeyStatistics', 'enterpriseToEbitda', 'raw')
    }
    return record


def create_yahoo_price_data():
    tickers = get_all_yahoo_tickers()
    data = []
    for ticker_tuple in tickers:
        if len(ticker_tuple) == 2:
            try:
                record = get_yahoo_data(*ticker_tuple)
            except Exception:
                logger.error('Something went wrong getting ticker %s' % ticker_tuple[1])
                continue
            data.append(record)
        else:
            continue
    return data


class StockValuationETL(ETLBase):

    def job():
        data = create_yahoo_price_data()
        ETLBase.load_data(Price, data)
