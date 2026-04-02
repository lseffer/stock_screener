from abc import ABC, abstractmethod
from utils.config import Session, logger
from traceback import format_exc
from typing import List
from utils.models import Base


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
            logger.error('Failed to persist record: %s' % format_exc())
            return False
        finally:
            session.close()

    @staticmethod
    def load_records(data: List[Base]) -> int:
        """Persist a batch of records, committing in chunks. Returns count of successful records."""
        if not data:
            logger.info('No data to load')
            return 0
        session = Session()
        loaded = 0
        for idx, record in enumerate(data):
            try:
                session.merge(record)
                loaded += 1
            except Exception:
                logger.warning('Skipping bad record: %s' % format_exc())
                session.rollback()
                continue
            if loaded > 0 and loaded % 100 == 0:
                session.commit()
                logger.info('Committed %s records' % loaded)
        session.commit()
        session.close()
        logger.info('Loaded %s/%s records' % (loaded, len(data)))
        return loaded

    @staticmethod
    @abstractmethod
    def job() -> None:
        pass
