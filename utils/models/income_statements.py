from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict
from utils import get_nested


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
    dw_modified = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def process_response(cls, response: Dict, isin: str) -> Base:
        record = {
            'isin': isin,
            'report_date': datetime.fromtimestamp(get_nested(response, 'endDate', 'raw')).date(),
            'total_revenue': get_nested(response, 'totalRevenue', 'raw'),
            'cost_of_revenue': get_nested(response, 'costOfRevenue', 'raw'),
            'gross_profit': get_nested(response, 'grossProfit', 'raw'),
            'research_development': get_nested(response, 'researchDevelopment', 'raw'),
            'selling_general_administrative': get_nested(response, 'sellingGeneralAdministrative', 'raw'),
            'non_recurring': get_nested(response, 'nonRecurring', 'raw'),
            'other_operating_expenses': get_nested(response, 'otherOperatingExpenses', 'raw'),
            'total_operating_expenses': get_nested(response, 'totalOperatingExpenses', 'raw'),
            'operating_income': get_nested(response, 'operatingIncome', 'raw'),
            'total_other_income_expense_net': get_nested(response, 'totalOtherIncomeExpenseNet', 'raw'),
            'ebit': get_nested(response, 'ebit', 'raw'),
            'interest_expense': get_nested(response, 'interestExpense', 'raw'),
            'income_before_tax': get_nested(response, 'incomeBeforeTax', 'raw'),
            'income_tax_expense': get_nested(response, 'incomeTaxExpense', 'raw'),
            'minority_interest': get_nested(response, 'minorityInterest', 'raw'),
            'net_income_from_continuing_ops': get_nested(response, 'netIncomeFromContinuingOps', 'raw'),
            'discontinued_operations': get_nested(response, 'discontinuedOperations', 'raw'),
            'extraordinary_items': get_nested(response, 'extraordinaryItems', 'raw'),
            'effect_of_accounting_charges': get_nested(response, 'effectOfAccountingCharges', 'raw'),
            'other_items': get_nested(response, 'otherItems', 'raw'),
            'net_income': get_nested(response, 'netIncome', 'raw'),
            'net_income_applicable_to_common_shares': get_nested(response, 'netIncomeApplicableToCommonShares', 'raw')
        }
        result: Base = cls(**record)
        return result
