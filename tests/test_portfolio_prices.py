import logging
import unittest

import numpy as np
import pandas as pd

from portfolio_opt.prices import align_and_clean, to_returns

log = logging.getLogger('test_portfolio_prices')
log.addHandler(logging.NullHandler())
log.propagate = False


def business_days(n, start='2022-01-03'):
    return pd.bdate_range(start, periods=n)


def make_panel(n=600, cols=('A', 'B')):
    idx = business_days(n)
    rng = np.random.default_rng(0)
    data = {c: 100 + np.cumsum(rng.normal(0, 1, size=n)) for c in cols}
    return pd.DataFrame(data, index=idx)


class TestAlignAndClean(unittest.TestCase):
    def test_clean_panel_passes_through(self):
        panel, dropped = align_and_clean(make_panel(), min_days=250, log=log)
        self.assertEqual(dropped, [])
        self.assertEqual(len(panel), 600)

    def test_ffill_bridges_short_gap_not_long(self):
        prices = make_panel()
        prices.loc[prices.index[100:103], 'B'] = np.nan   # 3-day gap: bridged
        prices.loc[prices.index[300:310], 'A'] = np.nan   # 10-day gap: not bridged
        panel, dropped = align_and_clean(prices, min_days=250, log=log)
        self.assertEqual(dropped, [])
        self.assertIn(prices.index[101], panel.index)
        # ffill limit is 5, so days 305..309 of the long gap stay NaN and drop.
        self.assertNotIn(prices.index[306], panel.index)
        self.assertGreater(len(panel), 500)

    def test_short_history_asset_dropped_not_panel_truncated(self):
        prices = make_panel(600, cols=('A', 'B', 'C'))
        prices.loc[prices.index[:550], 'C'] = np.nan  # C only has last 50 days
        panel, dropped = align_and_clean(prices, min_days=250, log=log)
        self.assertEqual([c for c, _ in dropped], ['C'])
        self.assertEqual(list(panel.columns), ['A', 'B'])
        self.assertEqual(len(panel), 600)

    def test_all_short_histories_kept_with_warning(self):
        # Both assets share a short window; dropping either doesn't help.
        prices = make_panel(100)
        panel, dropped = align_and_clean(prices, min_days=250, log=log)
        self.assertEqual(dropped, [])
        self.assertEqual(len(panel), 100)

    def test_too_few_rows_aborts(self):
        prices = make_panel(30)
        with self.assertRaises(ValueError):
            align_and_clean(prices, min_days=250, log=log)

    def test_single_column_aborts(self):
        prices = make_panel(600, cols=('A',))
        with self.assertRaises(ValueError):
            align_and_clean(prices, min_days=250, log=log)

    def test_empty_panel_aborts(self):
        with self.assertRaises(ValueError):
            align_and_clean(pd.DataFrame(), min_days=250, log=log)

    def test_leading_nans_truncated(self):
        prices = make_panel(600)
        prices.loc[prices.index[:50], 'B'] = np.nan
        panel, dropped = align_and_clean(prices, min_days=250, log=log)
        self.assertEqual(dropped, [])
        self.assertEqual(panel.index[0], prices.index[50])


class TestToReturns(unittest.TestCase):
    def test_simple_returns(self):
        prices = pd.DataFrame({'A': [100.0, 110.0, 99.0]}, index=business_days(3))
        returns = to_returns(prices)
        self.assertAlmostEqual(returns['A'].iloc[0], 0.10)
        self.assertAlmostEqual(returns['A'].iloc[1], -0.10)
        self.assertEqual(len(returns), 2)


if __name__ == '__main__':
    unittest.main()
