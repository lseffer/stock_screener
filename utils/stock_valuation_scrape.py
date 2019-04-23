import requests
from traceback import format_exc
from utils.models import Stock
from utils.config import Session, logger

YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}"


def get_all_yahoo_tickers():
    session = Session()
    res = session.query(Stock.yahoo_ticker).all()
    # Remember this is a list of tuples
    return res


def get_yahoo_data(yahoo_ticker):
    params = {"formatted": "false",
              "lang": "en-US",
              "region": "US",
              "modules": "summaryDetail,financialData,defaultKeyStatistics",
              "corsDomain": "finance.yahoo.com"}
    response = requests.get(YAHOO_FINANCE_BASE_URL.format(yahoo_ticker), params=params).json()
    record = {
        'price': response['financialData']['currentPrice'].get('raw', None),
        'target_median_price': response['financialData']['targetMedianPrice'].get('raw', None),
        'recommendation': response['financialData']['recommendationKey'].get('raw', None),
        'number_of_analyst_opinions': response['financialData']['numberOfAnalystOpinions'].get('raw', None),
        'ebitda': response['financialData']['ebitda'].get('raw', None),
        'market_cap': response['summaryDetail']['marketCap'].get('raw', None),
        'trailing_pe': response['summaryDetail']['trailingPE'].get('raw', None),
        'forward_pe': response['summaryDetail']['forwardPE'].get('raw', None),
        'ev_ebitda_ratio': response['defaultKeyStatistics']['enterpriseToEbitda'].get('raw', None)
    }
    return record

