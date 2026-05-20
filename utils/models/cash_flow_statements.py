from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict, Any
import pandas as pd


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

    FIELD_MAP = {
        'Net Income': 'net_income',
        'Net Income From Continuing Operations': 'net_income',
        'Depreciation And Amortization': 'change_to_netincome',
        'Change To Netincome': 'change_to_netincome',
        'Change In Account Receivable': 'change_to_account_receivables',
        'Change To Account Receivables': 'change_to_account_receivables',
        'Changes In Account Receivables': 'change_to_account_receivables',
        'Change To Liabilities': 'change_to_liabilities',
        'Change In Other Working Capital': 'change_to_liabilities',
        'Operating Cash Flow': 'total_cash_from_operating_activities',
        'Total Cash From Operating Activities': 'total_cash_from_operating_activities',
        'Capital Expenditure': 'capital_expenditures',
        'Capital Expenditures': 'capital_expenditures',
        'Other Cash Flows From Investing Activities': 'other_cashflows_from_investing_activities',
        'Investing Cash Flow': 'total_cashflows_from_investing_activities',
        'Total Cashflows From Investing Activities': 'total_cashflows_from_investing_activities',
        'Common Stock Dividend Paid': 'dividends_paid',
        'Dividends Paid': 'dividends_paid',
        'Net Borrowings': 'net_borrowings',
        'Net Issuance Payments Of Debt': 'net_borrowings',
        'Other Cash Flows From Financing Activities': 'other_cashflows_from_financing_activities',
        'Financing Cash Flow': 'total_cash_from_financing_activities',
        'Total Cash From Financing Activities': 'total_cash_from_financing_activities',
        'Effect Of Exchange Rate': 'effect_of_exchange_rate',
        'Effect Of Exchange Rate Changes': 'effect_of_exchange_rate',
        'Changes In Cash': 'change_in_cash',
        'Change In Cash': 'change_in_cash',
        'Change In Cash Supplemental As Reported': 'change_in_cash',
        'Repurchase Of Capital Stock': 'repurchase_of_stock',
        'Repurchase Of Stock': 'repurchase_of_stock',
        'Common Stock Issuance': 'issuance_of_stock',
        'Issuance Of Stock': 'issuance_of_stock',
        'Net Common Stock Issuance': 'issuance_of_stock',
    }

    @classmethod
    def from_yfinance_column(cls, df: pd.DataFrame, col_date: Any, isin: str) -> 'CashFlowStatement':
        series = df[col_date].dropna()
        record: Dict[str, Any] = {'isin': isin, 'report_date': col_date.date() if hasattr(col_date, 'date') else col_date}
        for yf_label, our_field in cls.FIELD_MAP.items():
            if yf_label in series.index and our_field not in record:
                record[our_field] = float(series[yf_label])
        return cls(**record)
