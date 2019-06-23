import unittest
from utils.models import Stock

class TestStockInfoScraper(unittest.TestCase):

    mock_record = {
        'isin': 'FISHIT',
        'symbol': 'shit',
        'currency': 'EUR',
        'name': 'test',
        'sector': 'crap'
    }

    def test_normal_get_yahoo_ticker(self):
        res = Stock.parse_yahoo_ticker_from_isin(self.mock_record)
        self.assertEqual(res, 'shit.HE')

    def test_crazy_get_yahoo_ticker(self):
        mk_rec = self.mock_record.copy()
        mk_rec['isin'] = 'ZZ'
        mk_rec['currency'] = 'NOK'
        res = Stock.parse_yahoo_ticker_from_isin(mk_rec)
        self.assertEqual(res, 'shit.OL')
