import yfinance as yf
from utils.queries import fetch_all_tickers_from_database, fetch_tickers_needing_financials
from utils import union_of_list_elements
from utils.models import Base, BalanceSheetStatement, CashFlowStatement, IncomeStatement
from utils.config import logger
from utils.etl_base import ETLBase
from typing import List
import time


class StockFinancialStatementsETL(ETLBase):

    @staticmethod
    def job() -> None:
        all_tickers = fetch_all_tickers_from_database()

        # Find ISINs missing data for any of the three statement types
        needs_income = fetch_tickers_needing_financials(IncomeStatement)
        needs_balance = fetch_tickers_needing_financials(BalanceSheetStatement)
        needs_cashflow = fetch_tickers_needing_financials(CashFlowStatement)
        tickers_to_fetch = union_of_list_elements(needs_income, needs_balance, needs_cashflow)

        skipped = len(all_tickers) - len(tickers_to_fetch)
        logger.info(
            'Skipping %s stocks with current financials, fetching %s'
            % (skipped, len(tickers_to_fetch))
        )

        data: List[Base] = []
        for isin, yahoo_ticker in tickers_to_fetch:
            if not yahoo_ticker:
                continue
            try:
                ticker = yf.Ticker(yahoo_ticker)

                income_df = ticker.income_stmt
                if income_df is not None and not income_df.empty:
                    for col_date in income_df.columns:
                        try:
                            data.append(IncomeStatement.from_yfinance_column(income_df, col_date, isin))
                        except Exception as e:
                            logger.warning('Failed income stmt %s/%s: %s' % (yahoo_ticker, col_date, e))

                bs_df = ticker.balance_sheet
                if bs_df is not None and not bs_df.empty:
                    for col_date in bs_df.columns:
                        try:
                            data.append(BalanceSheetStatement.from_yfinance_column(bs_df, col_date, isin))
                        except Exception as e:
                            logger.warning('Failed balance sheet %s/%s: %s' % (yahoo_ticker, col_date, e))

                cf_df = ticker.cashflow
                if cf_df is not None and not cf_df.empty:
                    for col_date in cf_df.columns:
                        try:
                            data.append(CashFlowStatement.from_yfinance_column(cf_df, col_date, isin))
                        except Exception as e:
                            logger.warning('Failed cashflow %s/%s: %s' % (yahoo_ticker, col_date, e))

                logger.debug('Got financials for %s' % yahoo_ticker)
            except Exception as e:
                logger.error('Failed to get financials for %s: %s' % (yahoo_ticker, e))
                continue
            time.sleep(0.5)

        logger.info('Fetched %s financial statement records' % len(data))
        ETLBase.load_data(data)
