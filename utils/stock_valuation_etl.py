import yfinance as yf
from utils.queries import fetch_all_tickers_from_database, fetch_tickers_needing_price_update
from utils.models import Base, Price
from utils.config import logger
from utils.etl_base import ETLBase
from typing import List
import time


class StockValuationETL(ETLBase):

    @staticmethod
    def job() -> None:
        all_tickers = fetch_all_tickers_from_database()
        stale_tickers = fetch_tickers_needing_price_update(max_age_days=5)
        skipped = len(all_tickers) - len(stale_tickers)
        logger.info('Skipping %s stocks with recent prices, fetching %s' % (skipped, len(stale_tickers)))

        data: List[Base] = []
        for isin, yahoo_ticker in stale_tickers:
            if not yahoo_ticker:
                continue
            try:
                ticker = yf.Ticker(yahoo_ticker)
                info = ticker.info
                if not info or info.get('regularMarketPrice') is None and info.get('currentPrice') is None:
                    logger.warning('No data for %s' % yahoo_ticker)
                    continue
                record = Price.from_yfinance(info, isin)
                data.append(record)
                logger.debug('Got price data for %s' % yahoo_ticker)
            except Exception as e:
                logger.error('Failed to get price for %s: %s' % (yahoo_ticker, e))
                continue
            time.sleep(0.5)
        logger.info('Fetched price data for %s stocks' % len(data))
        ETLBase.load_data(data)
