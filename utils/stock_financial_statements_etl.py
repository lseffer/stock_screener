from utils import fetch_yahoo_data, get_nested
from utils.queries import fetch_all_tickers_from_database
from utils.models import Base, BalanceSheetStatement, CashFlowStatement, IncomeStatement
from utils.config import logger
from utils.etl_base import ETLBase
from typing import Dict, List, Tuple
from traceback import format_exc


def create_database_records() -> List[Base]:
    tickers: List[Tuple] = fetch_all_tickers_from_database()
    data = []
    for ticker_tuple in tickers:
        if len(ticker_tuple) == 2:
            isin = ticker_tuple[0]
            yahoo_ticker = ticker_tuple[1]
            try:
                response = fetch_yahoo_data(yahoo_ticker,
                                            'balanceSheetHistory,incomeStatementHistory,cashflowStatementHistory')
                income_statement_response: List = get_nested(response,
                                                             'incomeStatementHistory', 'incomeStatementHistory',
                                                             default=[])
                cash_flow_statement_response: List = get_nested(response,
                                                                'cashflowStatementHistory', 'cashflowStatements',
                                                                default=[])
                balance_sheet_statement_response: List = get_nested(response,
                                                                    'balanceSheetHistory', 'balanceSheetStatements',
                                                                    default=[])
                for response in income_statement_response:
                    data.append(IncomeStatement.process_response(response, isin))
                for response in cash_flow_statement_response:
                    data.append(CashFlowStatement.process_response(response, isin))
                for response in balance_sheet_statement_response:
                    data.append(BalanceSheetStatement.process_response(response, isin))
            except Exception:
                logger.error('Something went wrong getting ticker %s' % yahoo_ticker)
                logger.error(format_exc)
                continue
            data.append(record)
        else:
            continue
    return data


class IncomeStatementETL(ETLBase):

    @staticmethod
    def job() -> None:
        data = create_yahoo_data(fetch_yahoo_price_data)
        ETLBase.load_data(data)
