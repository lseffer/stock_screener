from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from typing import Dict
from utils import get_nested


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
    dw_modified = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def process_response(cls, response: Dict, isin: str) -> Base:
        record = {
            'isin': isin,
            'report_date': datetime.fromtimestamp(get_nested(response, 'endDate', 'raw')).date(),
            'cash': get_nested(response, 'cash', 'raw'),
            'short_term_investments': get_nested(response, 'shortTermInvestments', 'raw'),
            'net_receivables': get_nested(response, 'netReceivables', 'raw'),
            'total_current_assets': get_nested(response, 'totalCurrentAssets', 'raw'),
            'property_plant_equipment': get_nested(response, 'propertyPlantEquipment', 'raw'),
            'intangible_assets': get_nested(response, 'intangibleAssets', 'raw'),
            'other_assets': get_nested(response, 'otherAssets', 'raw'),
            'deferred_long_term_asset_charges': get_nested(response, 'deferredLongTermAssetCharges', 'raw'),
            'total_assets': get_nested(response, 'totalAssets', 'raw'),
            'accounts_payable': get_nested(response, 'accountsPayable', 'raw'),
            'short_long_term_debt': get_nested(response, 'shortLongTermDebt', 'raw'),
            'other_current_liab': get_nested(response, 'otherCurrentLiab', 'raw'),
            'long_term_debt': get_nested(response, 'longTermDebt', 'raw'),
            'other_liab': get_nested(response, 'otherLiab', 'raw'),
            'deferred_long_term_liab': get_nested(response, 'deferredLongTermLiab', 'raw'),
            'total_current_liabilities': get_nested(response, 'totalCurrentLiabilities', 'raw'),
            'total_liab': get_nested(response, 'totalLiab', 'raw'),
            'common_stock': get_nested(response, 'commonStock', 'raw'),
            'retained_earnings': get_nested(response, 'retainedEarnings', 'raw'),
            'treasury_stock': get_nested(response, 'treasuryStock', 'raw'),
            'other_stockholder_equity': get_nested(response, 'otherStockholderEquity', 'raw'),
            'total_stockholder_equity': get_nested(response, 'totalStockholderEquity', 'raw'),
            'net_tangible_assets': get_nested(response, 'netTangibleAssets', 'raw')
        }
        result: Base = cls(**record)
        return result
