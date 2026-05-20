import unittest

import polars as pl

from scoring import (
    _add_cap_tier,
    _add_market_cap_eur,
    _add_percentile_ranks,
    _add_shareholder_yield_total,
)


class TestMarketCapEur(unittest.TestCase):
    def test_converts_native_currency_to_eur(self):
        df = pl.DataFrame({
            'currency': ['EUR', 'SEK', 'DKK', 'XYZ', None],
            'market_cap': [1_000.0, 1_000.0, 1_000.0, 1_000.0, 1_000.0],
        })
        out = _add_market_cap_eur(df)
        eur = out['market_cap_eur'].to_list()
        self.assertEqual(eur[0], 1_000.0)
        self.assertAlmostEqual(eur[1], 87.0, places=3)
        self.assertAlmostEqual(eur[2], 134.0, places=3)
        self.assertIsNone(eur[3])
        self.assertIsNone(eur[4])


class TestCapTier(unittest.TestCase):
    def test_tier_assignment(self):
        df = pl.DataFrame({
            'market_cap_eur': [
                6_000_000_000,    # large
                2_000_000_000,    # mid
                400_000_000,      # small
                50_000_000,       # micro
                None,             # null
            ]
        })
        out = _add_cap_tier(df)
        self.assertEqual(
            out['cap_tier'].to_list(),
            ['large', 'mid', 'small', 'micro', None],
        )


class TestShareholderYieldTotal(unittest.TestCase):
    def test_sum_with_nulls(self):
        df = pl.DataFrame({
            'shareholder_yield_stock': [0.03, None, 0.01, None],
            'shareholder_yield_dividends': [0.02, 0.04, None, None],
        })
        out = _add_shareholder_yield_total(df)
        total = out['shareholder_yield_total'].to_list()
        self.assertAlmostEqual(total[0], 0.05)
        self.assertAlmostEqual(total[1], 0.04)
        self.assertAlmostEqual(total[2], 0.01)
        self.assertIsNone(total[3])


class TestPercentileRanks(unittest.TestCase):
    def test_ranks_in_expected_range(self):
        df = pl.DataFrame({
            'magic_formula_score': [0.5, 1.0, None, 2.0, 3.0],
            'roic': [0.05, None, 0.20, 0.15, 0.10],
            'shareholder_yield_total': [0.01, 0.02, 0.03, None, 0.05],
        })
        out = _add_percentile_ranks(df)
        for col in (
            'magic_formula_score_percentile',
            'roic_percentile',
            'shareholder_yield_percentile',
        ):
            self.assertIn(col, out.columns)
            values = [v for v in out[col].to_list() if v is not None]
            self.assertTrue(all(0 < v <= 100 for v in values))
            self.assertAlmostEqual(max(values), 100.0)

        magic = out['magic_formula_score_percentile'].to_list()
        self.assertIsNone(magic[2])
        self.assertEqual(magic[4], 100.0)


if __name__ == '__main__':
    unittest.main()
