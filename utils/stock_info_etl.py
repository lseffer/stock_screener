import yfinance as yf
from yfinance import EquityQuery
from utils.models import Stock
from utils.etl_base import ETLBase
from utils.config import get_logger
from typing import Dict, List

logger = get_logger('stock_info')

# Yahoo Finance exchange codes for Nordic markets
NORDIC_EXCHANGES = {
    'STO': 'Stockholm',
    'CPH': 'Copenhagen',
    'HEL': 'Helsinki',
    'OSL': 'Oslo',
}

MAX_PER_PAGE = 250


def fetch_exchange_stocks(exchange_code: str) -> List[Dict]:
    """Fetch all stocks for a given exchange using the yfinance screener, handling pagination."""
    query = EquityQuery('is-in', ['exchange', exchange_code])
    all_quotes = []
    offset = 0

    while True:
        result = yf.screen(query, sortField='ticker', sortAsc=True, size=MAX_PER_PAGE, offset=offset)
        quotes = result.get('quotes', [])
        if not quotes:
            break
        all_quotes.extend(quotes)
        total = result.get('count', 0)
        offset += len(quotes)
        if offset >= total:
            break

    return all_quotes


class StockInfoETL(ETLBase):

    @staticmethod
    def job() -> None:
        total = 0
        for exchange_code, exchange_name in NORDIC_EXCHANGES.items():
            logger.info('Fetching stock list for %s (%s)', exchange_name, exchange_code)
            try:
                quotes = fetch_exchange_stocks(exchange_code)
                logger.info('Found %s stocks on %s', len(quotes), exchange_name)
            except Exception as e:
                logger.exception('Failed to fetch %s stock list: %s', exchange_name, e)
                continue

            loaded = 0
            for quote in quotes:
                symbol = quote.get('symbol', '?')
                try:
                    record = Stock.from_yfinance_screener(quote)
                    if record.yahoo_ticker:
                        ETLBase.load_record(record)
                        total += 1
                        loaded += 1
                except Exception as e:
                    logger.warning('[%s] failed to process quote: %s', symbol, e)
            logger.info('Loaded %s stocks from %s', loaded, exchange_name)

        logger.info('Stock info ETL complete: %s stocks loaded', total)
