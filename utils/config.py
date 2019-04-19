import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

HOME = os.environ.get('HOME', None)
POSTGRES_USER = os.environ.get('POSTGRES_USER', None)
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', None)
POSTGRES_DB = os.environ.get('POSTGRES_DB', None)


def setup_logging(level=logging.INFO):
    log = logging.getLogger()
    log.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
