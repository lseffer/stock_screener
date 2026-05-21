import os
import sys
import logging
from datetime import datetime, date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_last_year() -> date:
    return date(datetime.utcnow().year - 1, 12, 31)


DB_PATH = os.getenv('STOCK_SCREENER_DB', 'stocks.db')
OUTPUT_DIR = os.getenv('STOCK_SCREENER_OUTPUT', '_site')


def create_sqlite_engine() -> Engine:
    engine = create_engine(f'sqlite:///{DB_PATH}')
    return engine


engine = create_sqlite_engine()
Session = sessionmaker(bind=engine)


_PACKAGE_LOGGER = 'stock_screener'
_LOG_FORMAT = '%(asctime)s [%(levelname)-5s] %(name)s: %(message)s'
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _resolve_level(level):
    if level is not None:
        return level
    raw = os.getenv('STOCK_SCREENER_LOG_LEVEL', 'INFO').upper()
    return getattr(logging, raw, logging.INFO)


def setup_logging(level=None) -> logging.Logger:
    """Configure the package logger. Idempotent: safe to call multiple times."""
    log = logging.getLogger(_PACKAGE_LOGGER)
    log.setLevel(_resolve_level(level))
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        log.addHandler(handler)
        log.propagate = False
    return log


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the ``stock_screener`` namespace.

    Pass a short, descriptive name like ``"valuation"`` rather than ``__name__``
    so the log output stays grep-able.
    """
    setup_logging()
    if not name or name == _PACKAGE_LOGGER:
        return logging.getLogger(_PACKAGE_LOGGER)
    return logging.getLogger(f'{_PACKAGE_LOGGER}.{name}')


class _TickerAdapter(logging.LoggerAdapter):
    """Logger adapter that prefixes every message with the bound ticker."""

    def process(self, msg, kwargs):
        return f"[{self.extra['ticker']}] {msg}", kwargs


def bind_ticker(log: logging.Logger, ticker: str) -> logging.LoggerAdapter:
    """Wrap ``log`` so every emitted message is prefixed with ``[ticker]``."""
    return _TickerAdapter(log, {'ticker': ticker})


logger = setup_logging()
