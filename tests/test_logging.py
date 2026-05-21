import logging
import unittest

from utils.config import bind_ticker, get_logger, setup_logging


class TestLoggingSetup(unittest.TestCase):
    def test_setup_is_idempotent(self):
        a = setup_logging()
        b = setup_logging()
        self.assertIs(a, b)
        self.assertEqual(len(a.handlers), 1, 'duplicate handlers added on repeated calls')

    def test_get_logger_creates_child_under_package(self):
        log = get_logger('valuation')
        self.assertEqual(log.name, 'stock_screener.valuation')
        self.assertIs(log.parent, logging.getLogger('stock_screener'))

    def test_bind_ticker_prefixes_messages(self):
        log = get_logger('valuation')
        adapter = bind_ticker(log, 'ERIC-B.ST')

        records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                records.append(record)

        capture = _Capture()
        log.addHandler(capture)
        try:
            adapter.info('fetched price %s', 152.30)
        finally:
            log.removeHandler(capture)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].getMessage(), '[ERIC-B.ST] fetched price 152.3')


if __name__ == '__main__':
    unittest.main()
