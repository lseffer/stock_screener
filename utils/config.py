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


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    log = logging.getLogger('stock_screener')
    log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(level)
    log.addHandler(stdout_handler)

    return log


logger = setup_logging(logging.INFO)
