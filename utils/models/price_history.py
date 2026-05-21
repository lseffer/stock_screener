from utils.models.base import Base
from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime


class PriceHistory(Base):
    __tablename__ = 'price_history'
    isin = Column(String, primary_key=True)
    market_date = Column(Date, primary_key=True)
    close_price = Column(Float)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
