from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict, Any
import pandas as pd


class BalanceSheetStatement(Base):
    __tablename__ = 'balance_sheet_statements'
    isin = Column(String, primary_key=True)
    report_date = Column(Date, primary_key=True)
    cash = Column(Float)
    short_term_investments = Column(Float)
    net_receivables = Column(Float)
    total_current_assets = Column(Float)
    property_plant_equipment = Column(Float)
    intangible_assets = Column(Float)
    other_assets = Column(Float)
    deferred_long_term_asset_charges = Column(Float)
    total_assets = Column(Float)
    accounts_payable = Column(Float)
    short_long_term_debt = Column(Float)
    other_current_liab = Column(Float)
    long_term_debt = Column(Float)
    other_liab = Column(Float)
    deferred_long_term_liab = Column(Float)
    total_current_liabilities = Column(Float)
    total_liab = Column(Float)
    common_stock = Column(Float)
    retained_earnings = Column(Float)
    treasury_stock = Column(Float)
    other_stockholder_equity = Column(Float)
    total_stockholder_equity = Column(Float)
    net_tangible_assets = Column(Float)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    FIELD_MAP = {
        'Cash And Cash Equivalents': 'cash',
        'Cash': 'cash',
        'Cash Cash Equivalents And Short Term Investments': 'cash',
        'Short Term Investments': 'short_term_investments',
        'Other Short Term Investments': 'short_term_investments',
        'Net Receivables': 'net_receivables',
        'Receivables': 'net_receivables',
        'Current Assets': 'total_current_assets',
        'Total Current Assets': 'total_current_assets',
        'Net PPE': 'property_plant_equipment',
        'Property Plant Equipment': 'property_plant_equipment',
        'Goodwill And Other Intangible Assets': 'intangible_assets',
        'Intangible Assets': 'intangible_assets',
        'Other Assets': 'other_assets',
        'Other Non Current Assets': 'other_assets',
        'Total Assets': 'total_assets',
        'Accounts Payable': 'accounts_payable',
        'Current Debt': 'short_long_term_debt',
        'Current Debt And Capital Lease Obligation': 'short_long_term_debt',
        'Short Long Term Debt': 'short_long_term_debt',
        'Other Current Liabilities': 'other_current_liab',
        'Long Term Debt': 'long_term_debt',
        'Long Term Debt And Capital Lease Obligation': 'long_term_debt',
        'Other Liabilities': 'other_liab',
        'Other Non Current Liabilities': 'other_liab',
        'Current Liabilities': 'total_current_liabilities',
        'Total Current Liabilities': 'total_current_liabilities',
        'Total Liabilities Net Minority Interest': 'total_liab',
        'Total Liab': 'total_liab',
        'Common Stock': 'common_stock',
        'Common Stock Equity': 'common_stock',
        'Retained Earnings': 'retained_earnings',
        'Treasury Stock': 'treasury_stock',
        'Treasury Shares Number': 'treasury_stock',
        'Other Stockholder Equity': 'other_stockholder_equity',
        'Stockholders Equity': 'total_stockholder_equity',
        'Total Stockholder Equity': 'total_stockholder_equity',
        'Net Tangible Assets': 'net_tangible_assets',
        'Tangible Book Value': 'net_tangible_assets',
    }

    @classmethod
    def from_yfinance_column(cls, df: pd.DataFrame, col_date: Any, isin: str) -> 'BalanceSheetStatement':
        series = df[col_date].dropna()
        record: Dict[str, Any] = {'isin': isin, 'report_date': col_date.date() if hasattr(col_date, 'date') else col_date}
        for yf_label, our_field in cls.FIELD_MAP.items():
            if yf_label in series.index and our_field not in record:
                record[our_field] = float(series[yf_label])
        return cls(**record)
