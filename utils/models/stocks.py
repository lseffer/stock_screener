from utils.models.base import Base
from sqlalchemy import Column, String, DateTime
from datetime import datetime
from typing import Dict


class Stock(Base):
    __tablename__ = 'stocks'
    isin = Column(String, primary_key=True)
    name = Column(String)
    symbol = Column(String)
    currency = Column(String)
    sector = Column(String)
    yahoo_ticker = Column(String)
    dw_created = Column(DateTime, default=datetime.utcnow)
    dw_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def parse_yahoo_ticker_from_isin(record: Dict[str, str]) -> str:
        symbol: str = record.get('symbol', '').replace(' ', '-')
        isin_country: str = record.get('isin', '')[:2]
        currency: str = record.get('currency', '')
        if isin_country == 'DK':
            return symbol + '.CO'
        elif isin_country == 'SE':
            return symbol + '.ST'
        elif isin_country == 'FI':
            return symbol + '.HE'
        elif isin_country == 'NO':
            return symbol.replace('o', '') + '.OL'
        elif currency == 'DKK':
            return symbol + '.CO'
        elif currency == 'ISK':
            return symbol + '.CO'
        elif currency == 'SEK':
            return symbol + '.ST'
        elif currency == 'EUR':
            return symbol + '.HE'
        elif currency == 'NOK':
            return symbol.replace('o', '') + '.OL'
        else:
            return ''

    @classmethod
    def from_scraped_row(cls, values: list) -> 'Stock':
        record: Dict[str, str] = {
            'isin': values[3],
            'name': values[0],
            'symbol': values[1],
            'currency': values[2],
            'sector': values[4]
        }
        record['yahoo_ticker'] = cls.parse_yahoo_ticker_from_isin(record.copy())
        return cls(**record)
