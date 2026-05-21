import time
from typing import List

import yfinance as yf

from utils import union_of_list_elements
from utils.config import bind_ticker, get_logger
from utils.etl_base import ETLBase
from utils.models import Base, BalanceSheetStatement, CashFlowStatement, IncomeStatement
from utils.queries import fetch_all_tickers_from_database, fetch_tickers_needing_financials

logger = get_logger('financials')


class StockFinancialStatementsETL(ETLBase):

    @staticmethod
    def job() -> None:
        all_tickers = fetch_all_tickers_from_database()

        needs_income = fetch_tickers_needing_financials(IncomeStatement)
        needs_balance = fetch_tickers_needing_financials(BalanceSheetStatement)
        needs_cashflow = fetch_tickers_needing_financials(CashFlowStatement)
        tickers_to_fetch = union_of_list_elements(needs_income, needs_balance, needs_cashflow)

        skipped = len(all_tickers) - len(tickers_to_fetch)
        total = len(tickers_to_fetch)
        logger.info(
            'Skipping %s stocks with current financials, fetching %s',
            skipped, total,
        )

        fetched = 0
        failed = 0
        for idx, (isin, yahoo_ticker) in enumerate(tickers_to_fetch, start=1):
            if not yahoo_ticker:
                continue
            log = bind_ticker(logger, yahoo_ticker)
            progress = f'[{idx}/{total}]'
            try:
                ticker = yf.Ticker(yahoo_ticker)
                records: List[Base] = []
                counts = {'income': 0, 'balance': 0, 'cashflow': 0}

                income_df = ticker.income_stmt
                if income_df is not None and not income_df.empty:
                    for col_date in income_df.columns:
                        try:
                            records.append(IncomeStatement.from_yfinance_column(income_df, col_date, isin))
                            counts['income'] += 1
                        except Exception as e:
                            log.warning('income stmt %s skipped: %s', col_date, e)

                bs_df = ticker.balance_sheet
                if bs_df is not None and not bs_df.empty:
                    for col_date in bs_df.columns:
                        try:
                            records.append(BalanceSheetStatement.from_yfinance_column(bs_df, col_date, isin))
                            counts['balance'] += 1
                        except Exception as e:
                            log.warning('balance sheet %s skipped: %s', col_date, e)

                cf_df = ticker.cashflow
                if cf_df is not None and not cf_df.empty:
                    for col_date in cf_df.columns:
                        try:
                            records.append(CashFlowStatement.from_yfinance_column(cf_df, col_date, isin))
                            counts['cashflow'] += 1
                        except Exception as e:
                            log.warning('cashflow %s skipped: %s', col_date, e)

                loaded = ETLBase.load_records(records)
                if loaded > 0:
                    fetched += 1
                    log.info(
                        '%s loaded %s statements (income=%s balance=%s cashflow=%s)',
                        progress, loaded, counts['income'], counts['balance'], counts['cashflow'],
                    )
                else:
                    failed += 1
                    log.warning('%s no statements available', progress)
            except Exception as e:
                log.exception('%s fetch failed: %s', progress, e)
                failed += 1
                continue
            time.sleep(0.1)

        logger.info(
            'Financials ETL complete: %s fetched, %s failed (of %s)',
            fetched, failed, total,
        )
