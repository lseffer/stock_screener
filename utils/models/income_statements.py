from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict, Any
import pandas as pd


class IncomeStatement(Base):
    __tablename__ = 'income_statements'
    isin = Column(String, primary_key=True)
    report_date = Column(Date, primary_key=True)
    total_revenue = Column(Float)
    cost_of_revenue = Column(Float)
    gross_profit = Column(Float)
    research_development = Column(Float)
    selling_general_administrative = Column(Float)
    non_recurring = Column(Float)
    other_operating_expenses = Column(Float)
    total_operating_expenses = Column(Float)
    operating_income = Column(Float)
    total_other_income_expense_net = Column(Float)
    ebit = Column(Float)
    interest_expense = Column(Float)
    income_before_tax = Column(Float)
    income_tax_expense = Column(Float)
    minority_interest = Column(Float)
    net_income_from_continuing_ops = Column(Float)
    discontinued_operations = Column(Float)
    extraordinary_items = Column(Float)
    effect_of_accounting_charges = Column(Float)
    other_items = Column(Float)
    net_income = Column(Float)
    net_income_applicable_to_common_shares = Column(Float)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Mapping from yfinance row labels to our column names
    FIELD_MAP = {
        'Total Revenue': 'total_revenue',
        'Cost Of Revenue': 'cost_of_revenue',
        'Gross Profit': 'gross_profit',
        'Research And Development': 'research_development',
        'Research Development': 'research_development',
        'Selling General And Administration': 'selling_general_administrative',
        'Selling General Administrative': 'selling_general_administrative',
        'Other Operating Expenses': 'other_operating_expenses',
        'Total Operating Expenses': 'total_operating_expenses',
        'Operating Income': 'operating_income',
        'Total Other Income Expense Net': 'total_other_income_expense_net',
        'Other Income Expense': 'total_other_income_expense_net',
        'EBIT': 'ebit',
        'Interest Expense': 'interest_expense',
        'Pretax Income': 'income_before_tax',
        'Income Before Tax': 'income_before_tax',
        'Tax Provision': 'income_tax_expense',
        'Income Tax Expense': 'income_tax_expense',
        'Minority Interest': 'minority_interest',
        'Net Income From Continuing Ops': 'net_income_from_continuing_ops',
        'Net Income From Continuing Operations': 'net_income_from_continuing_ops',
        'Net Income From Continuing Operation Net Minority Interest': 'net_income_from_continuing_ops',
        'Discontinued Operations': 'discontinued_operations',
        'Extraordinary Items': 'extraordinary_items',
        'Net Income': 'net_income',
        'Net Income Common Stockholders': 'net_income_applicable_to_common_shares',
        'Net Income Applicable To Common Shares': 'net_income_applicable_to_common_shares',
    }

    @classmethod
    def from_yfinance_column(cls, df: pd.DataFrame, col_date: Any, isin: str) -> 'IncomeStatement':
        series = df[col_date].dropna()
        record: Dict[str, Any] = {'isin': isin, 'report_date': col_date.date() if hasattr(col_date, 'date') else col_date}
        for yf_label, our_field in cls.FIELD_MAP.items():
            if yf_label in series.index:
                record[our_field] = float(series[yf_label])
        return cls(**record)
