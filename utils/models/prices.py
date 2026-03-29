from utils.models.base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime, date
from typing import Dict, Any


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
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def from_yfinance(cls, info: Dict[str, Any], isin: str) -> 'Price':
        return cls(
            isin=isin,
            market_date=date.today(),
            price=info.get('currentPrice'),
            target_median_price=info.get('targetMedianPrice'),
            recommendation=info.get('recommendationMean'),
            number_of_analyst_opinions=info.get('numberOfAnalystOpinions'),
            ebitda=info.get('ebitda'),
            market_cap=info.get('marketCap'),
            trailing_pe=info.get('trailingPE'),
            forward_pe=info.get('forwardPE'),
            ev_ebitda_ratio=info.get('enterpriseToEbitda'),
        )
