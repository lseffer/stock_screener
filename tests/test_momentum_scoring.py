import unittest
from datetime import date

import polars as pl

from scoring import compute_momentum_scores, _add_value_momentum_score


def _monthly_series(start_year: int, start_month: int, n: int):
    out = []
    y, m = start_year, start_month
    for _ in range(n):
        out.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


class TestComputeMomentumScores(unittest.TestCase):
    def test_returns_expected_values_for_full_history(self):
        # 14 monthly bars: closes 100, 101, 102, ..., 113
        dates = _monthly_series(2025, 1, 14)
        closes = [100.0 + i for i in range(14)]
        df = pl.DataFrame({
            'isin': ['ABC.ST'] * 14,
            'market_date': dates,
            'close_price': closes,
        })

        out = compute_momentum_scores(df)

        self.assertEqual(out.height, 1)
        row = out.row(0, named=True)
        self.assertEqual(row['isin'], 'ABC.ST')
        self.assertEqual(row['market_date'], dates[-1])
        # close[t]=113, close[t-1]=112, close[t-3]=110, close[t-6]=107, close[t-13]=100
        self.assertAlmostEqual(row['return_12_1'], 112.0 / 100.0 - 1.0)
        self.assertAlmostEqual(row['return_6m'], 113.0 / 107.0 - 1.0)
        self.assertAlmostEqual(row['return_3m'], 113.0 / 110.0 - 1.0)
        expected_score = (row['return_12_1'] + row['return_6m'] + row['return_3m']) / 3.0
        self.assertAlmostEqual(row['momentum_score'], expected_score)

    def test_short_history_yields_null_long_term_returns(self):
        # Only 5 monthly bars — too short for 12-1 and 6-month returns
        dates = _monthly_series(2025, 1, 5)
        closes = [100.0, 102.0, 104.0, 106.0, 110.0]
        df = pl.DataFrame({
            'isin': ['SHORT.ST'] * 5,
            'market_date': dates,
            'close_price': closes,
        })

        out = compute_momentum_scores(df)

        self.assertEqual(out.height, 1)
        row = out.row(0, named=True)
        self.assertIsNone(row['return_12_1'])
        self.assertIsNone(row['return_6m'])
        # 3-month return is computable: close[t]=110, close[t-3]=102
        self.assertAlmostEqual(row['return_3m'], 110.0 / 102.0 - 1.0)
        # momentum_score is the mean of available returns (mean_horizontal ignores nulls)
        self.assertAlmostEqual(row['momentum_score'], row['return_3m'])

    def test_multiple_tickers_returns_one_row_each(self):
        dates = _monthly_series(2025, 1, 14)
        closes_a = [100.0 + i for i in range(14)]
        closes_b = [200.0 - i for i in range(14)]  # falling prices
        df = pl.DataFrame({
            'isin': ['A.ST'] * 14 + ['B.ST'] * 14,
            'market_date': dates + dates,
            'close_price': closes_a + closes_b,
        })

        out = compute_momentum_scores(df).sort('isin')

        self.assertEqual(out.height, 2)
        self.assertEqual(out['isin'].to_list(), ['A.ST', 'B.ST'])
        # A should have positive momentum, B negative
        self.assertGreater(out.row(0, named=True)['momentum_score'], 0)
        self.assertLess(out.row(1, named=True)['momentum_score'], 0)

    def test_empty_input_returns_empty_dataframe_with_schema(self):
        empty = pl.DataFrame(schema={
            'isin': pl.String,
            'market_date': pl.Date,
            'close_price': pl.Float64,
        })
        out = compute_momentum_scores(empty)
        self.assertEqual(out.height, 0)
        for col in ('isin', 'market_date', 'return_12_1', 'return_6m', 'return_3m', 'momentum_score'):
            self.assertIn(col, out.columns)


class TestValueMomentumScore(unittest.TestCase):
    def test_averages_percentiles_when_both_present(self):
        df = pl.DataFrame({
            'magic_formula_score_percentile': [100.0, 50.0, None, 25.0],
            'momentum_score_percentile': [50.0, None, 80.0, 75.0],
        })
        out = _add_value_momentum_score(df)
        vm = out['value_momentum_score'].to_list()
        self.assertAlmostEqual(vm[0], 75.0)
        self.assertIsNone(vm[1])
        self.assertIsNone(vm[2])
        self.assertAlmostEqual(vm[3], 50.0)


if __name__ == '__main__':
    unittest.main()
