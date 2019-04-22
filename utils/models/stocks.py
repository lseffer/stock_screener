from .base import Base
from sqlalchemy import Column, String, DateTime
from datetime import datetime

class Stocks(Base):
    __tablename__ = 'stocks'
    isin = Column(String, primary_key=True)
    name = Column(String)
    symbol = Column(String)
    currency = Column(String)
    sector = Column(String)
    yahoo_ticker = Column(String)
    dw_created = Column(DateTime, default=datetime.now())
    dw_modified = Column(DateTime, default=datetime.now())
