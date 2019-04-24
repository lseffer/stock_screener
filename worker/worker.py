import time
import threading
from traceback import format_exc
import datetime
from schedule import Scheduler
from utils.config import logger
from utils.stock_info_scraper import scrape_stock_info_export_to_pg
from utils.stock_valuation_scrape import yahoo_price_data_export_to_pg


class SafeScheduler(Scheduler):
    """
    An implementation of Scheduler that catches jobs that fail, logs their
    exception tracebacks as errors, optionally reschedules the jobs for their
    next run time, and keeps going.
    Use this to run jobs that may or may not crash without worrying about
    whether other jobs will run or if they'll crash the entire script.
    """

    def __init__(self, reschedule_on_failure=True, logger=None):
        """
        If reschedule_on_failure is True, jobs will be rescheduled for their
        next run as if they had completed successfully. If False, they'll run
        on the next run_pending() tick.
        """
        self.logger = logger
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        try:
            super()._run_job(job)
        except Exception:
            if self.logger:
                self.logger.error(format_exc())
            job.last_run = datetime.datetime.now()
            job._schedule_next_run()


def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()


def job():
    print("I'm working...")


if __name__ == '__main__':
    scheduler = SafeScheduler(logger=logger)
    scheduler.every(10).seconds.do(run_threaded, job)
    scheduler.every().saturday.at("00:00").do(run_threaded, scrape_stock_info_export_to_pg)
    scheduler.every().day.at("23:00").do(run_threaded, yahoo_price_data_export_to_pg)
    while True:
        logger.debug('Heartbeat 5 seconds')
        scheduler.run_pending()
        time.sleep(5)
