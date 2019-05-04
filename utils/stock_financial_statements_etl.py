from utils import fetch_yahoo_data, get_nested, union_of_list_elements
from utils.queries import fetch_isins_not_updated_financials
from utils.models import Base, BalanceSheetStatement, CashFlowStatement, IncomeStatement
from utils.config import logger
from utils.etl_base import ETLBase
from typing import Dict, List, Tuple, Union, Any
from traceback import format_exc


def fetch_yahoo_responses() -> List[Tuple]:
    tickers: List[List] = []
    for model in [IncomeStatement, BalanceSheetStatement, CashFlowStatement]:
        tickers.append(fetch_isins_not_updated_financials(model))  # type: ignore
    tickers_unique: List[Tuple] = union_of_list_elements(*tickers)
    logger.info('Fetching financials from %s stocks' % len(tickers_unique))
    responses: List[Tuple[Any, ...]] = []
    for ticker_tuple in tickers_unique:
        if len(ticker_tuple) == 2:
            isin: str = ticker_tuple[0]
            yahoo_ticker: str = ticker_tuple[1]
            try:
                response = fetch_yahoo_data(yahoo_ticker,
                                            'balanceSheetHistory,incomeStatementHistory,cashflowStatementHistory')
                logger.info('Succeeded getting ticker, isin: %s, %s' % (yahoo_ticker, isin))
            except Exception:
                logger.error('Something went wrong getting ticker, isin: %s, %s' % (yahoo_ticker, isin))
                logger.error(format_exc())
                continue
            responses.append((response, isin))
        else:
            continue
    return responses


def traverse_statement_history(Model: Union[IncomeStatement,
                                            BalanceSheetStatement,
                                            CashFlowStatement],
                               isin: str,
                               statements: List[Dict]) -> List[Base]:
    data = []
    for statement in statements:
        data.append(Model.process_response(statement, isin))
    return data


class StockFinancialStatementsETL(ETLBase):

    @staticmethod
    def job() -> None:
        data: List[Base] = []
        responses: List[Tuple] = fetch_yahoo_responses()
        for response in responses:
            payload: Dict = response[0]
            isin: str = response[1]
            income_statement_response: List = get_nested(payload,
                                                         'incomeStatementHistory', 'incomeStatementHistory',
                                                         default=[])
            data = data + traverse_statement_history(Model=IncomeStatement,  # type: ignore
                                                     isin=isin, statements=income_statement_response)
            cash_flow_statement_response: List = get_nested(payload,
                                                            'cashflowStatementHistory', 'cashflowStatements',
                                                            default=[])
            data = data + traverse_statement_history(Model=CashFlowStatement,  # type: ignore
                                                     isin=isin, statements=cash_flow_statement_response)
            balance_sheet_statement_response: List = get_nested(payload,
                                                                'balanceSheetHistory', 'balanceSheetStatements',
                                                                default=[])
            data = data + traverse_statement_history(Model=BalanceSheetStatement,  # type: ignore
                                                     isin=isin, statements=balance_sheet_statement_response)
        ETLBase.load_data(data)
