import time
import threading
import logging
import sys
from traceback import format_exc
import datetime
from schedule import Scheduler


def setup_logging():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


logger = setup_logging()


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
    scheduler.every(5).seconds.do(run_threaded, job)
    scheduler.every(10).seconds.do(run_threaded, job)
    while True:
        logger.info('Heartbeat 5 seconds')
        scheduler.run_pending()
        time.sleep(5)
