import os
import sys
import logging
from datetime import datetime, date
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

LAST_YEAR = date(datetime.utcnow().year - 1, 12, 31)

HOME = os.environ.get('HOME', None)
POSTGRES_USER = os.environ.get('POSTGRES_USER', None)
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', None)
POSTGRES_DB = os.environ.get('POSTGRES_DB', None)

YAHOO_API_BASE_URL = "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{}"
YAHOO_API_PARAMS = {"formatted": "false",
                    "lang": "en-US",
                    "region": "US",
                    "corsDomain": "finance.yahoo.com"}


def create_pg_engine():
    engine = create_engine('postgresql://%s:%s@database/%s' %
                           (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB))
    return engine


engine = create_pg_engine()
Session = sessionmaker(bind=engine)


def setup_logging(level=logging.INFO):
    log = logging.getLogger()
    log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(level)

    timed_filehandler = TimedRotatingFileHandler('%s/worker.log' % HOME, when='D', interval=14)
    timed_filehandler.setFormatter(formatter)
    timed_filehandler.setLevel(level)

    log.addHandler(stdout_handler)
    log.addHandler(timed_filehandler)
    return log


logger = setup_logging(logging.DEBUG)
