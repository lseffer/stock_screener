from abc import ABC, abstractmethod
from utils.config import Session, logger
from traceback import format_exc
from typing import List
from utils.models import Base

class ETLBase(ABC):

    @staticmethod
    def load_data(data: List[Base]) -> None:
        if len(data) > 0:
            session = Session()
            for idx, record in enumerate(data):
                try:
                    session.merge(record)
                except Exception:
                    logger.info('Something went wrong: %s' % record)
                    logger.error(format_exc())
                    continue
                logger.debug(record)
                if idx > 0 and idx % 100 == 0:
                    session.commit()
                    logger.info('Chunked commit at %s records' % idx)
            session.commit()
            logger.info('Chunked commit at %s records' % idx)
            session.close()
        else:
            logger.info('No data to load')

    @abstractmethod
    def job() -> None:
        pass
