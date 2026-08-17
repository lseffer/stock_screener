import unittest

import numpy as np

from portfolio_opt.optimizer import (
    TRADING_DAYS,
    annualize,
    efficient_frontier,
    max_sharpe,
    max_utility,
    min_variance,
    optimize,
    portfolio_stats,
)


def two_asset_inputs(sigma1=0.10, sigma2=0.20, mu1=0.05, mu2=0.10):
    mu = np.array([mu1, mu2])
    cov = np.array([[sigma1 ** 2, 0.0], [0.0, sigma2 ** 2]])
    return mu, cov


class TestMinVariance(unittest.TestCase):
    def test_two_uncorrelated_assets_analytic(self):
        # w1 = sigma2^2 / (sigma1^2 + sigma2^2)
        mu, cov = two_asset_inputs(sigma1=0.10, sigma2=0.20)
        point = min_variance(mu, cov, rf=0.02)
        expected_w1 = 0.20 ** 2 / (0.10 ** 2 + 0.20 ** 2)
        self.assertAlmostEqual(point.weights[0], expected_w1, places=4)
        self.assertAlmostEqual(point.weights.sum(), 1.0, places=8)

    def test_weights_within_bounds(self):
        mu, cov = two_asset_inputs()
        point = min_variance(mu, cov, rf=0.02, max_weight=0.6)
        self.assertTrue(np.all(point.weights >= -1e-9))
        self.assertTrue(np.all(point.weights <= 0.6 + 1e-9))


class TestMaxSharpe(unittest.TestCase):
    def test_two_uncorrelated_assets_analytic(self):
        # Tangency weights proportional to (mu_i - rf) / sigma_i^2 for diagonal cov.
        rf = 0.02
        mu, cov = two_asset_inputs(sigma1=0.10, sigma2=0.20, mu1=0.06, mu2=0.12)
        raw = np.array([(0.06 - rf) / 0.10 ** 2, (0.12 - rf) / 0.20 ** 2])
        expected = raw / raw.sum()
        point = max_sharpe(mu, cov, rf=rf)
        np.testing.assert_allclose(point.weights, expected, atol=1e-3)

    def test_sharpe_beats_other_portfolios(self):
        mu = np.array([0.04, 0.09, 0.13])
        cov = np.array([
            [0.02, 0.005, 0.001],
            [0.005, 0.05, 0.01],
            [0.001, 0.01, 0.09],
        ])
        rf = 0.02
        best = max_sharpe(mu, cov, rf)
        for w in [np.array([1, 0, 0]), np.array([0.2, 0.5, 0.3]), np.full(3, 1 / 3)]:
            _, _, sharpe = portfolio_stats(w, mu, cov, rf)
            self.assertGreaterEqual(best.sharpe, sharpe - 1e-6)

    def test_max_weight_cap_binds(self):
        rf = 0.02
        # Second asset dominates: uncapped optimizer would allocate most weight there.
        mu, cov = two_asset_inputs(sigma1=0.20, sigma2=0.10, mu1=0.03, mu2=0.15)
        point = max_sharpe(mu, cov, rf=rf, max_weight=0.6)
        self.assertAlmostEqual(point.weights[1], 0.6, places=3)

    def test_negative_excess_returns_still_solve(self):
        mu, cov = two_asset_inputs(mu1=-0.02, mu2=-0.01)
        point = max_sharpe(mu, cov, rf=0.02)
        self.assertAlmostEqual(point.weights.sum(), 1.0, places=6)
        self.assertLess(point.sharpe, 0)


class TestMaxUtility(unittest.TestCase):
    def test_zero_risk_aversion_is_max_return(self):
        mu, cov = two_asset_inputs(mu1=0.05, mu2=0.10)
        point = max_utility(mu, cov, rf=0.02, risk_aversion=0.0)
        np.testing.assert_allclose(point.weights, [0.0, 1.0], atol=1e-6)

    def test_high_risk_aversion_approaches_min_variance(self):
        mu, cov = two_asset_inputs()
        point = max_utility(mu, cov, rf=0.02, risk_aversion=1e5)
        mv = min_variance(mu, cov, rf=0.02)
        np.testing.assert_allclose(point.weights, mv.weights, atol=1e-3)

    def test_two_uncorrelated_assets_analytic(self):
        # Interior optimum of mu@w - (lam/2) w@cov@w with sum-to-one constraint:
        # w_i = mu_i/(lam*sigma_i^2) + kappa/sigma_i^2 where kappa makes sum(w)=1.
        lam = 3.0
        mu, cov = two_asset_inputs(sigma1=0.10, sigma2=0.20, mu1=0.06, mu2=0.10)
        inv_var = np.array([1 / 0.10 ** 2, 1 / 0.20 ** 2])
        raw = mu * inv_var / lam
        kappa = (1.0 - raw.sum()) / inv_var.sum()
        expected = raw + kappa * inv_var
        point = max_utility(mu, cov, rf=0.02, risk_aversion=lam)
        np.testing.assert_allclose(point.weights, expected, atol=1e-3)

    def test_utility_beats_alternatives(self):
        lam = 2.5
        mu = np.array([0.04, 0.09, 0.13])
        cov = np.array([
            [0.02, 0.005, 0.001],
            [0.005, 0.05, 0.01],
            [0.001, 0.01, 0.09],
        ])
        best = max_utility(mu, cov, rf=0.02, risk_aversion=lam)
        best_u = best.ret - lam / 2 * best.vol ** 2
        for w in [np.array([1, 0, 0]), np.array([0.2, 0.5, 0.3]), np.full(3, 1 / 3)]:
            ret, vol, _ = portfolio_stats(w, mu, cov, rf=0.02)
            self.assertGreaterEqual(best_u, ret - lam / 2 * vol ** 2 - 1e-6)

    def test_lower_risk_aversion_takes_more_volatility(self):
        mu, cov = two_asset_inputs(mu1=0.05, mu2=0.12)
        bold = max_utility(mu, cov, rf=0.02, risk_aversion=1.0)
        cautious = max_utility(mu, cov, rf=0.02, risk_aversion=6.0)
        self.assertGreaterEqual(bold.vol, cautious.vol - 1e-9)
        self.assertGreaterEqual(bold.ret, cautious.ret - 1e-9)


class TestFrontier(unittest.TestCase):
    def test_starts_at_min_variance_and_is_monotonic(self):
        mu, cov = two_asset_inputs()
        rf = 0.02
        frontier = efficient_frontier(mu, cov, rf, n_points=20)
        self.assertGreater(len(frontier), 5)
        mv = min_variance(mu, cov, rf)
        self.assertAlmostEqual(frontier[0][0], mv.vol, places=4)
        vols = [v for v, _ in frontier]
        rets = [r for _, r in frontier]
        self.assertEqual(rets, sorted(rets))
        # Above the min-variance point, volatility weakly increases with return.
        self.assertTrue(all(vols[i + 1] >= vols[i] - 1e-9 for i in range(len(vols) - 1)))


class TestAnnualizeAndEdgeCases(unittest.TestCase):
    def test_annualize_scales_by_trading_days(self):
        rng = np.random.default_rng(42)
        daily = rng.normal(0.0005, 0.01, size=(1000, 2))
        mu, cov = annualize(daily)
        np.testing.assert_allclose(mu, daily.mean(axis=0) * TRADING_DAYS, rtol=1e-10)
        self.assertAlmostEqual(cov[0, 0], daily[:, 0].var(ddof=1) * TRADING_DAYS, places=6)

    def test_singular_covariance_survives(self):
        rng = np.random.default_rng(7)
        series = rng.normal(0.0005, 0.01, size=1000)
        daily = np.column_stack([series, series])  # perfectly correlated
        mu, cov = annualize(daily)
        point = max_sharpe(mu, cov, rf=0.02)
        self.assertAlmostEqual(point.weights.sum(), 1.0, places=6)

    def test_single_asset_trivial(self):
        rng = np.random.default_rng(1)
        daily = rng.normal(0.0005, 0.01, size=(500, 1))
        result = optimize(['ONLY'], daily, np.array([1.0]), rf=0.02)
        np.testing.assert_allclose(result.max_sharpe.weights, [1.0])
        np.testing.assert_allclose(result.min_variance.weights, [1.0])
        np.testing.assert_allclose(result.preferred.weights, [1.0])
        self.assertEqual(len(result.frontier), 1)

    def test_optimize_full_result(self):
        rng = np.random.default_rng(3)
        daily = np.column_stack([
            rng.normal(0.0006, 0.010, size=750),
            rng.normal(0.0004, 0.008, size=750),
            rng.normal(0.0008, 0.015, size=750),
        ])
        current = np.array([0.5, 0.3, 0.2])
        result = optimize(['A', 'B', 'C'], daily, current, rf=0.02, risk_aversion=1.5)
        self.assertEqual(result.labels, ['A', 'B', 'C'])
        self.assertEqual(result.risk_aversion, 1.5)
        self.assertAlmostEqual(result.preferred.weights.sum(), 1.0, places=8)
        self.assertEqual(result.corr.shape, (3, 3))
        np.testing.assert_allclose(np.diag(result.corr), 1.0, atol=1e-9)
        self.assertAlmostEqual(result.current.weights.sum(), 1.0, places=8)
        self.assertGreaterEqual(result.max_sharpe.sharpe, result.current.sharpe - 1e-6)
        self.assertLessEqual(result.min_variance.vol, result.current.vol + 1e-9)


if __name__ == '__main__':
    unittest.main()
