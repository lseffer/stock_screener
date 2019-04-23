from .base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime

class Price(Base):
    __tablename__ = 'prices'
    yahoo_ticker = Column(String, primary_key=True)
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
