from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict
from utils import get_nested


class CashFlowStatement(Base):
    __tablename__ = 'cash_flow_statements'
    isin = Column(String, primary_key=True)
    report_date = Column(Date, primary_key=True)
    net_income = Column(Float)
    change_to_netincome = Column(Float)
    change_to_account_receivables = Column(Float)
    change_to_liabilities = Column(Float)
    total_cash_from_operating_activities = Column(Float)
    capital_expenditures = Column(Float)
    other_cashflows_from_investing_activities = Column(Float)
    total_cashflows_from_investing_activities = Column(Float)
    dividends_paid = Column(Float)
    net_borrowings = Column(Float)
    other_cashflows_from_financing_activities = Column(Float)
    total_cash_from_financing_activities = Column(Float)
    effect_of_exchange_rate = Column(Float)
    change_in_cash = Column(Float)
    repurchase_of_stock = Column(Float)
    issuance_of_stock = Column(Float)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def process_response(cls, response: Dict, isin: str) -> Base:
        record = {
            'isin': isin,
            'report_date': datetime.fromtimestamp(get_nested(response, 'endDate', 'raw')).date(),
            'net_income': get_nested(response, 'netIncome', 'raw'),
            'change_to_netincome': get_nested(response, 'changeToNetincome', 'raw'),
            'change_to_account_receivables': get_nested(response, 'changeToAccountReceivables', 'raw'),
            'change_to_liabilities': get_nested(response, 'changeToLiabilities', 'raw'),
            'total_cash_from_operating_activities': get_nested(response, 'totalCashFromOperatingActivities', 'raw'),
            'capital_expenditures': get_nested(response, 'capitalExpenditures', 'raw'),
            'other_cashflows_from_investing_activities': get_nested(response, 'otherCashflowsFromInvestingActivities', 'raw'),
            'total_cashflows_from_investing_activities': get_nested(response, 'totalCashflowsFromInvestingActivities', 'raw'),
            'dividends_paid': get_nested(response, 'dividendsPaid', 'raw'),
            'net_borrowings': get_nested(response, 'netBorrowings', 'raw'),
            'other_cashflows_from_financing_activities': get_nested(response, 'otherCashflowsFromFinancingActivities', 'raw'),
            'total_cash_from_financing_activities': get_nested(response, 'totalCashFromFinancingActivities', 'raw'),
            'effect_of_exchange_rate': get_nested(response, 'effectOfExchangeRate', 'raw'),
            'change_in_cash': get_nested(response, 'changeInCash', 'raw'),
            'repurchase_of_stock': get_nested(response, 'repurchaseOfStock', 'raw'),
            'issuance_of_stock': get_nested(response, 'issuanceOfStock', 'raw')
        }
        result: Base = cls(**record)
        return result
