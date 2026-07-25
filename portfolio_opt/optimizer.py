"""Markowitz mean-variance optimization: max-Sharpe, min-variance, efficient frontier.

Pure numpy/scipy math on a daily-returns matrix. No IO, no yfinance — testable
with synthetic data just like scoring.py.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize

TRADING_DAYS = 252


@dataclass
class PortfolioPoint:
    weights: np.ndarray
    ret: float
    vol: float
    sharpe: float


@dataclass
class OptimizationResult:
    labels: List[str]
    mu: np.ndarray            # annualized expected returns per asset
    cov: np.ndarray           # annualized covariance matrix
    corr: np.ndarray
    asset_vols: np.ndarray    # annualized per-asset volatility
    current: PortfolioPoint
    max_sharpe: PortfolioPoint
    min_variance: PortfolioPoint
    frontier: List[Tuple[float, float]]  # (vol, ret) pairs


def annualize(daily_returns: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Annualized mean vector and covariance matrix from a (days, assets) matrix."""
    daily_returns = np.asarray(daily_returns, dtype=float)
    if daily_returns.ndim == 1:
        daily_returns = daily_returns.reshape(-1, 1)
    mu = daily_returns.mean(axis=0) * TRADING_DAYS
    if daily_returns.shape[1] == 1:
        cov = np.array([[daily_returns[:, 0].var(ddof=1) * TRADING_DAYS]])
    else:
        cov = np.cov(daily_returns, rowvar=False, ddof=1) * TRADING_DAYS
    return mu, _regularize(cov)


def _regularize(cov: np.ndarray) -> np.ndarray:
    """Add a tiny ridge when the covariance is near-singular (e.g. two holdings
    tracking the same index), so the optimizer does not blow up."""
    scale = float(np.mean(np.diag(cov)))
    if scale <= 0:
        scale = 1e-8
    min_eig = float(np.linalg.eigvalsh(cov).min())
    if min_eig <= 1e-12 * scale:
        cov = cov + 1e-8 * scale * np.eye(cov.shape[0])
    return cov


def portfolio_stats(w: np.ndarray, mu: np.ndarray, cov: np.ndarray, rf: float) -> Tuple[float, float, float]:
    w = np.asarray(w, dtype=float)
    ret = float(mu @ w)
    vol = float(np.sqrt(max(w @ cov @ w, 0.0)))
    sharpe = (ret - rf) / vol if vol > 0 else float('nan')
    return ret, vol, sharpe


def _point(w: np.ndarray, mu: np.ndarray, cov: np.ndarray, rf: float) -> PortfolioPoint:
    w = np.clip(np.asarray(w, dtype=float), 0.0, None)
    total = w.sum()
    if total > 0:
        w = w / total
    ret, vol, sharpe = portfolio_stats(w, mu, cov, rf)
    return PortfolioPoint(weights=w, ret=ret, vol=vol, sharpe=sharpe)


def _solve(objective, n: int, max_weight: float, extra_constraints=()) -> Optional[np.ndarray]:
    constraints = [{'type': 'eq', 'fun': lambda w: w.sum() - 1.0}]
    constraints.extend(extra_constraints)
    x0 = np.full(n, 1.0 / n)
    result = minimize(
        objective, x0, method='SLSQP',
        bounds=[(0.0, max_weight)] * n,
        constraints=constraints,
        options={'maxiter': 500, 'ftol': 1e-12},
    )
    return result.x if result.success else None


def min_variance(mu: np.ndarray, cov: np.ndarray, rf: float, max_weight: float = 1.0) -> PortfolioPoint:
    n = len(mu)
    if n == 1:
        return _point(np.array([1.0]), mu, cov, rf)
    w = _solve(lambda w: w @ cov @ w, n, max_weight)
    if w is None:
        w = np.full(n, 1.0 / n)
    return _point(w, mu, cov, rf)


def max_sharpe(mu: np.ndarray, cov: np.ndarray, rf: float, max_weight: float = 1.0) -> PortfolioPoint:
    n = len(mu)
    if n == 1:
        return _point(np.array([1.0]), mu, cov, rf)

    def neg_sharpe(w):
        ret = mu @ w
        vol = np.sqrt(max(w @ cov @ w, 1e-16))
        return -(ret - rf) / vol

    w = _solve(neg_sharpe, n, max_weight)
    if w is not None:
        return _point(w, mu, cov, rf)
    # Fall back to the best point on a coarse frontier grid.
    best = None
    for _, _, fw in _frontier_grid(mu, cov, rf, 25, max_weight):
        candidate = _point(fw, mu, cov, rf)
        if best is None or candidate.sharpe > best.sharpe:
            best = candidate
    return best if best is not None else min_variance(mu, cov, rf, max_weight)


def _max_return(mu: np.ndarray, cov: np.ndarray, max_weight: float) -> np.ndarray:
    n = len(mu)
    w = _solve(lambda w: -(mu @ w), n, max_weight)
    if w is None:
        w = np.full(n, 1.0 / n)
    return w


def _frontier_grid(mu, cov, rf, n_points, max_weight):
    """Yield (vol, ret, weights) frontier points between min-var and max return."""
    n = len(mu)
    low = min_variance(mu, cov, rf, max_weight)
    high_w = _max_return(mu, cov, max_weight)
    high_ret = float(mu @ high_w)
    targets = np.linspace(low.ret, high_ret, n_points)
    for target in targets:
        w = _solve(
            lambda w: w @ cov @ w, n, max_weight,
            extra_constraints=[{'type': 'eq', 'fun': lambda w, t=target: mu @ w - t}],
        )
        if w is None:
            continue
        ret, vol, _ = portfolio_stats(w, mu, cov, rf)
        yield vol, ret, w


def efficient_frontier(mu: np.ndarray, cov: np.ndarray, rf: float,
                       n_points: int = 40, max_weight: float = 1.0) -> List[Tuple[float, float]]:
    if len(mu) == 1:
        ret, vol, _ = portfolio_stats(np.array([1.0]), mu, cov, rf)
        return [(vol, ret)]
    return [(vol, ret) for vol, ret, _ in _frontier_grid(mu, cov, rf, n_points, max_weight)]


def optimize(labels: List[str], daily_returns: np.ndarray, current_weights: np.ndarray,
             rf: float, max_weight: float = 1.0) -> OptimizationResult:
    mu, cov = annualize(daily_returns)
    asset_vols = np.sqrt(np.diag(cov))
    denom = np.outer(asset_vols, asset_vols)
    denom[denom == 0] = 1.0
    corr = cov / denom
    return OptimizationResult(
        labels=list(labels),
        mu=mu,
        cov=cov,
        corr=corr,
        asset_vols=asset_vols,
        current=_point(current_weights, mu, cov, rf),
        max_sharpe=max_sharpe(mu, cov, rf, max_weight),
        min_variance=min_variance(mu, cov, rf, max_weight),
        frontier=efficient_frontier(mu, cov, rf, max_weight=max_weight),
    )
