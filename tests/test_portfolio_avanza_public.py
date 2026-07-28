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

    def test_mobile_top_hits_shape(self):
        payload = {
            'totalNumberOfHits': 1,
            'hits': [{'instrumentType': 'FUND', 'numberOfHits': 1,
                      'topHits': [{'id': '325406', 'name': 'Avanza Zero'}]}],
        }
        self.assertEqual(_extract_orderbook_id(payload), '325406')

    def test_fund_hits_preferred_over_other_types(self):
        payload = {
            'resultGroups': [
                {'instrumentType': 'STOCK', 'hits': [{'link': {'orderbookId': '111'}}]},
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

    def test_percent_development_series_rebased(self):
        # Fund-guide chart rebases to 0% at window start; +10% then -5%.
        day = 1704153600000
        payload = {'dataSerie': [
            {'x': day, 'y': 0.0},
            {'x': day + 86400000, 'y': 10.0},
            {'x': day + 2 * 86400000, 'y': -5.0},
        ]}
        series = parse_nav_payload(payload)
        values = [series[k] for k in sorted(series)]
        self.assertAlmostEqual(values[0], 1.00)
        self.assertAlmostEqual(values[1], 1.10)
        self.assertAlmostEqual(values[2], 0.95)

    def test_nav_series_kept_as_is(self):
        day = 1704153600000
        payload = {'dataSerie': [
            {'x': day, 'y': 123.45},
            {'x': day + 86400000, 'y': 124.0},
        ]}
        values = sorted(parse_nav_payload(payload).values())
        self.assertAlmostEqual(values[0], 123.45)


if __name__ == '__main__':
    unittest.main()
