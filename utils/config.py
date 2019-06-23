import os
import sys
import logging
from datetime import datetime, date
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_last_year() -> date:
    return date(datetime.utcnow().year - 1, 12, 31)


APP_ENV = os.getenv('APP_ENV')
HOME = os.getenv('HOME', None)
POSTGRES_USER = os.getenv('POSTGRES_USER', None)
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
POSTGRES_DB = os.getenv('POSTGRES_DB', None)
POSTGRES_HOST = os.getenv('POSTGRES_HOST', None)

YAHOO_API_BASE_URL = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}"
YAHOO_API_PARAMS = {"formatted": "false",
                    "lang": "en-US",
                    "region": "US",
                    "corsDomain": "finance.yahoo.com"}


def create_pg_engine() -> Engine:
    engine = create_engine('postgresql://%s:%s@%s/%s' %
                           (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB))
    return engine


engine = create_pg_engine()
Session = sessionmaker(bind=engine)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    log = logging.getLogger()
    log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(funcName)s - %(levelname)s - %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(level)
    log.addHandler(stdout_handler)

    if APP_ENV != 'test':
        timed_filehandler = TimedRotatingFileHandler('%s/worker.log' % HOME, when='D', interval=14)
        timed_filehandler.setFormatter(formatter)
        timed_filehandler.setLevel(level)
        log.addHandler(timed_filehandler)

    return log


logger = setup_logging(logging.INFO)
