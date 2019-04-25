from abc import ABC, abstractmethod
from utils.config import Session, logger
from traceback import format_exc


class ETLBase(ABC):

    @staticmethod
    def load_data(model=None, data=None):
        session = Session()
        for idx, record in enumerate(data):
            try:
                session.merge(model(**record))
            except Exception:
                logger.debug('Something went wrong: %s' % record)
                logger.error(format_exc())
                continue
            logger.debug(record)
            if idx % 100 == 0:
                session.commit()
                logger.info('Chunked commit at %s records' % idx)
        session.commit()
        logger.info('Chunked commit at %s records' % idx)
        session.close()

    @staticmethod
    @abstractmethod
    def job():
        pass
