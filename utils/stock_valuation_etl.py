import time

import yfinance as yf

from utils.config import bind_ticker, get_logger
from utils.etl_base import ETLBase
from utils.models import Price
from utils.queries import fetch_all_tickers_from_database, fetch_tickers_needing_price_update

logger = get_logger('valuation')


class StockValuationETL(ETLBase):

    @staticmethod
    def job() -> None:
        all_tickers = fetch_all_tickers_from_database()
        stale_tickers = fetch_tickers_needing_price_update(max_age_days=5)
        skipped = len(all_tickers) - len(stale_tickers)
        total = len(stale_tickers)
        logger.info('Skipping %s stocks with recent prices, fetching %s', skipped, total)

        fetched = 0
        failed = 0
        for idx, (isin, yahoo_ticker) in enumerate(stale_tickers, start=1):
            if not yahoo_ticker:
                continue
            log = bind_ticker(logger, yahoo_ticker)
            progress = f'[{idx}/{total}]'
            try:
                info = yf.Ticker(yahoo_ticker).info
                price = (info or {}).get('regularMarketPrice') or (info or {}).get('currentPrice')
                if not info or price is None:
                    log.warning('%s no price data', progress)
                    failed += 1
                    continue
                record = Price.from_yfinance(info, isin)
                if ETLBase.load_record(record):
                    fetched += 1
                    log.info(
                        '%s fetched price %.2f %s (mkt cap %s)',
                        progress, price,
                        info.get('financialCurrency') or info.get('currency') or '?',
                        _compact(info.get('marketCap')),
                    )
                else:
                    failed += 1
                    log.warning('%s failed to persist price record', progress)
            except Exception as e:
                log.exception('%s fetch failed: %s', progress, e)
                failed += 1
                continue
            time.sleep(0.1)
        logger.info('Price ETL complete: %s fetched, %s failed (of %s)', fetched, failed, total)


def _compact(value):
    if value is None:
        return '?'
    abs_v = abs(value)
    for unit, threshold in (('T', 1e12), ('B', 1e9), ('M', 1e6), ('K', 1e3)):
        if abs_v >= threshold:
            return f'{value / threshold:.1f}{unit}'
    return f'{value:.0f}'
