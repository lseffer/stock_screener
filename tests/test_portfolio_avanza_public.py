import unittest
from datetime import date

from portfolio_opt.avanza_public import _extract_orderbook_id, parse_nav_payload


class TestExtractOrderbookId(unittest.TestCase):
    def test_hits_shape(self):
        payload = {'hits': [{'orderbookId': 325406, 'name': 'Avanza Zero'}]}
        self.assertEqual(_extract_orderbook_id(payload), '325406')

    def test_result_groups_shape(self):
        payload = {
            'resultGroups': [
                {'instrumentType': 'FUND', 'hits': [{'link': {'orderbookId': '325406'}}]},
            ]
        }
        self.assertEqual(_extract_orderbook_id(payload), '325406')

    def test_malformed_returns_none(self):
        self.assertIsNone(_extract_orderbook_id(None))
        self.assertIsNone(_extract_orderbook_id({}))
        self.assertIsNone(_extract_orderbook_id({'hits': ['garbage']}))
        self.assertIsNone(_extract_orderbook_id({'resultGroups': [{'hits': [{}]}]}))


class TestParseNavPayload(unittest.TestCase):
    def test_data_serie_shape(self):
        # 2024-01-02 UTC in epoch ms
        payload = {'dataSerie': [{'x': 1704153600000, 'y': 123.45}, {'x': 1704240000000, 'y': 124.0}]}
        series = parse_nav_payload(payload)
        self.assertEqual(len(series), 2)
        self.assertAlmostEqual(series[date.fromtimestamp(1704153600)], 123.45)

    def test_skips_null_points(self):
        payload = {'dataSerie': [{'x': 1704153600000, 'y': None}, {'x': None, 'y': 1.0}, 'junk']}
        self.assertEqual(parse_nav_payload(payload), {})

    def test_malformed_returns_empty(self):
        self.assertEqual(parse_nav_payload(None), {})
        self.assertEqual(parse_nav_payload({'other': 1}), {})
        self.assertEqual(parse_nav_payload([1, 2]), {})


if __name__ == '__main__':
    unittest.main()
