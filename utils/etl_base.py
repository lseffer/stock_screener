from abc import ABC, abstractmethod
from typing import List

from utils.config import Session, get_logger
from utils.models import Base

logger = get_logger('etl')


class ETLBase(ABC):

    @staticmethod
    def load_record(record: Base) -> bool:
        """Persist a single record to the database. Returns True on success."""
        session = Session()
        try:
            session.merge(record)
            session.commit()
            return True
        except Exception:
            session.rollback()
            logger.exception('Failed to persist %s', type(record).__name__)
            return False
        finally:
            session.close()

    @staticmethod
    def load_records(data: List[Base]) -> int:
        """Persist a batch of records, committing in chunks. Returns count of successful records."""
        if not data:
            return 0
        session = Session()
        loaded = 0
        for record in data:
            try:
                session.merge(record)
                loaded += 1
            except Exception:
                session.rollback()
                logger.exception('Skipping bad %s record', type(record).__name__)
                continue
            if loaded > 0 and loaded % 100 == 0:
                session.commit()
                logger.debug('Committed %s records (batch)', loaded)
        session.commit()
        session.close()
        logger.debug('Loaded %s/%s records', loaded, len(data))
        return loaded

    @staticmethod
    @abstractmethod
    def job() -> None:
        pass
