from utils.models.base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime
from utils import get_nested
from typing import Dict


class Price(Base):
    __tablename__ = 'prices'
    isin = Column(String, primary_key=True)
    market_date = Column(Date, primary_key=True)
    price = Column(Float)
    target_median_price = Column(Float)
    recommendation = Column(Float)
    number_of_analyst_opinions = Column(Float)
    ebitda = Column(Float)
    market_cap = Column(Float)
    trailing_pe = Column(Float)
    forward_pe = Column(Float)
    ev_ebitda_ratio = Column(Float)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow)

    @classmethod
    def process_response(cls, response: Dict, isin: str) -> Base:
        record = {
            'isin': isin,
            'market_date': datetime.fromtimestamp(get_nested(response, 'price', 'regularMarketTime')).date(),
            'price': get_nested(response, 'financialData', 'currentPrice', 'raw'),
            'target_median_price': get_nested(response, 'financialData', 'targetMedianPrice', 'raw'),
            'recommendation': get_nested(response, 'financialData', 'recommendationKey', 'raw'),
            'number_of_analyst_opinions': get_nested(response, 'financialData', 'numberOfAnalystOpinions', 'raw'),
            'ebitda': get_nested(response, 'financialData', 'ebitda', 'raw'),
            'market_cap': get_nested(response, 'summaryDetail', 'marketCap', 'raw'),
            'trailing_pe': get_nested(response, 'summaryDetail', 'trailingPE', 'raw'),
            'forward_pe': get_nested(response, 'summaryDetail', 'forwardPE', 'raw'),
            'ev_ebitda_ratio': get_nested(response, 'defaultKeyStatistics', 'enterpriseToEbitda', 'raw')
        }
        result: Base = cls(**record)
        return result
