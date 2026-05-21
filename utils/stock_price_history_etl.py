import time
from typing import List

import yfinance as yf

from utils.config import bind_ticker, get_logger
from utils.etl_base import ETLBase
from utils.models import Base, PriceHistory
from utils.queries import fetch_all_tickers_from_database, fetch_tickers_needing_price_history

logger = get_logger('price_history')


class StockPriceHistoryETL(ETLBase):
    """Fetches ~14 months of monthly close prices via yfinance.

    14 months is enough to compute 12-1 momentum (12-month return excluding
    the most recent month) with one bar of buffer. We re-fetch the whole window
    each run; the composite PK + SQLAlchemy session.merge in ETLBase handles
    idempotent upserts."""

    @staticmethod
    def job() -> None:
        all_tickers = fetch_all_tickers_from_database()
        stale_tickers = fetch_tickers_needing_price_history(max_age_days=25)
        skipped = len(all_tickers) - len(stale_tickers)
        total = len(stale_tickers)
        logger.info(
            'Skipping %s stocks with recent price history, fetching %s',
            skipped, total,
        )

        fetched = 0
        failed = 0
        for idx, (isin, yahoo_ticker) in enumerate(stale_tickers, start=1):
            if not yahoo_ticker:
                continue
            log = bind_ticker(logger, yahoo_ticker)
            progress = f'[{idx}/{total}]'
            try:
                hist = yf.Ticker(yahoo_ticker).history(
                    period='14mo', interval='1mo', auto_adjust=True,
                )
                if hist is None or hist.empty:
                    log.warning('%s no price history', progress)
                    failed += 1
                    continue
                records: List[Base] = []
                for ts, row in hist.iterrows():
                    close = row.get('Close')
                    if close is None or (isinstance(close, float) and close != close):
                        continue
                    records.append(PriceHistory(
                        isin=isin,
                        market_date=ts.date(),
                        close_price=float(close),
                    ))
                if not records:
                    log.warning('%s no valid close prices in history', progress)
                    failed += 1
                    continue
                loaded = ETLBase.load_records(records)
                if loaded > 0:
                    fetched += 1
                    log.info('%s loaded %s monthly bars', progress, loaded)
                else:
                    failed += 1
                    log.warning('%s failed to persist price history', progress)
            except Exception as e:
                log.exception('%s fetch failed: %s', progress, e)
                failed += 1
                continue
            time.sleep(0.1)

        logger.info(
            'Price history ETL complete: %s fetched, %s failed (of %s)',
            fetched, failed, total,
        )
