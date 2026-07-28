#!/usr/bin/env python3
"""Optimize your personal portfolio (Avanza + Nordea holdings) with Markowitz
mean-variance analysis: efficient frontier, max-Sharpe and min-variance weights.

Local and private by design: reads broker CSV exports from portfolio/ (gitignored),
fetches price history on demand, and writes a self-contained HTML report. Nothing
is stored in the screener database or published to _site/.

Usage:
    python optimize_portfolio.py                       # portfolio/*.csv, 3y history
    python optimize_portfolio.py --max-weight 0.25     # cap any single position
    python optimize_portfolio.py --risk-free 0.025 --years 5
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from utils.config import get_logger

logger = get_logger('portfolio')

PORTFOLIO_README = """\
Drop your broker position exports here (this folder is gitignored).

Supported files (any *.csv in this folder):
  - Avanza: positions export from the web UI (semicolon-separated, Swedish headers)
  - Nordea: positions export from netbank
  - Generic: name,isin,quantity,market_value,currency[,account]
      e.g.  Ericsson B,SE0000108656,100,8512.50,SEK,my-isk
      The isin may be left empty — the holding is then resolved by name via
      avanza.se's public search (works well for fund names like "Avanza Zero"):
            Avanza Zero,,300,75431.10,SEK

ticker_overrides.csv pins instruments the auto-resolution cannot find. The
first column is the ISIN, or the holding name for rows without one:
  isin,ticker
  SE0000108656,ERIC-B.ST          # a Yahoo Finance ticker
  SE0001718388,avanza:325406      # an avanza.se orderbook id (fund NAV history)
  Avanza Global,avanza:944976     # name-keyed override for a no-ISIN row
  SE0000000001,                   # empty ticker = exclude this holding

Then run:  python optimize_portfolio.py
"""

OVERRIDES_STUB = 'isin,ticker\n'


def ensure_portfolio_dir(portfolio_dir: Path) -> bool:
    """Create the portfolio dir with helper files on first run. Returns True if created."""
    if portfolio_dir.exists():
        return False
    portfolio_dir.mkdir(parents=True)
    (portfolio_dir / 'README.txt').write_text(PORTFOLIO_README)
    (portfolio_dir / 'ticker_overrides.csv').write_text(OVERRIDES_STUB)
    return True


def print_results(result, names, tickers, values_sek, excluded, total_sek):
    def line(text=''):
        print(text)

    line()
    line('=' * 78)
    line('PORTFOLIO OPTIMIZATION — %d holdings, %s total' % (len(names), _sek(total_sek)))
    line('=' * 78)
    header = '%-28s %-14s %8s %8s %8s %8s' % ('Holding', 'Source', 'Value%', 'Current', 'MaxShrp', 'MinVar')
    line(header)
    line('-' * len(header))
    order = np.argsort(-result.current.weights)
    for i in order:
        line('%-28s %-14s %7.1f%% %7.1f%% %7.1f%% %7.1f%%' % (
            names[i][:28], tickers[i][:14],
            100 * values_sek[i] / total_sek if total_sek else 0.0,
            100 * result.current.weights[i],
            100 * result.max_sharpe.weights[i],
            100 * result.min_variance.weights[i],
        ))
    line('-' * len(header))
    for label, point in (('Current', result.current), ('Max Sharpe', result.max_sharpe),
                         ('Min variance', result.min_variance)):
        line('%-14s return %6.1f%%   vol %6.1f%%   Sharpe %6.2f' % (
            label, 100 * point.ret, 100 * point.vol, point.sharpe))
    if excluded:
        line()
        line('Excluded from optimization:')
        for holding, reason in excluded:
            identity = ' (%s)' % holding.isin if holding.isin else ''
            line('  - %s%s: %s' % (holding.name, identity, reason))
        line('  Pin these in portfolio/ticker_overrides.csv (isin-or-name,ticker).')
    line()


def _sek(x):
    return '{:,.0f} kr'.format(x).replace(',', ' ')


def main():
    parser = argparse.ArgumentParser(description='Markowitz portfolio optimization over broker CSV exports')
    parser.add_argument('--portfolio-dir', default='portfolio', help='Folder with broker CSV exports (default: portfolio)')
    parser.add_argument('--years', type=int, default=3, help='Years of daily price history (default: 3)')
    parser.add_argument('--risk-free', type=float, default=0.02, help='Annual risk-free rate (default: 0.02)')
    parser.add_argument('--output', default='portfolio_report.html', help='HTML report path (default: portfolio_report.html)')
    parser.add_argument('--max-weight', type=float, default=1.0, help='Max weight per holding, 0-1 (default: 1.0)')
    parser.add_argument('--min-days', type=int, default=250, help='Preferred minimum common trading days (default: 250)')
    parser.add_argument('--no-cache', action='store_true', help='Ignore cached ISIN->ticker resolutions')
    args = parser.parse_args()

    from portfolio_opt.holdings import load_holdings, merge_holdings
    from portfolio_opt.optimizer import optimize
    from portfolio_opt.prices import align_and_clean, fetch_history, to_returns
    from portfolio_opt.report import render_report
    from portfolio_opt.resolve import ResolutionCache, load_overrides, resolve_all

    portfolio_dir = Path(args.portfolio_dir)
    if ensure_portfolio_dir(portfolio_dir):
        logger.info('Created %s/ with a README and ticker_overrides.csv stub. '
                    'Drop your Avanza/Nordea CSV exports there and re-run.', portfolio_dir)
        return 1

    try:
        holdings = load_holdings(portfolio_dir, logger)
    except (FileNotFoundError, ValueError) as exc:
        logger.error('%s', exc)
        return 1
    merged = merge_holdings(holdings, logger)
    if not merged:
        logger.error('No valid holdings found in %s/', portfolio_dir)
        return 1
    logger.info('Loaded %d holdings (%d rows) worth %s',
                len(merged), len(holdings), _sek(sum(m.market_value_sek for m in merged)))

    if not 0 < args.max_weight <= 1:
        logger.error('--max-weight must be in (0, 1]')
        return 1
    if args.max_weight * len(merged) < 1:
        logger.error('--max-weight %.2f is infeasible for %d holdings (cap x holdings must be >= 1)',
                     args.max_weight, len(merged))
        return 1

    overrides = load_overrides(portfolio_dir, logger)
    cache = ResolutionCache(portfolio_dir)
    if args.no_cache:
        cache._data = {}
    resolved, excluded = resolve_all(merged, overrides, cache, logger)
    if not resolved:
        logger.error('No holdings could be resolved to a price source. '
                     'Add entries to %s/ticker_overrides.csv.', portfolio_dir)
        return 1

    logger.info('Fetching %d years of daily history for %d instruments...', args.years, len(resolved))
    prices, failures = fetch_history(resolved, args.years, logger)
    by_key = {m.key: m for m in merged}
    for key, reason in failures:
        excluded.append((by_key[key], reason))
        cache.invalidate(key)
    if failures:
        cache.save()

    try:
        panel, dropped = align_and_clean(prices, args.min_days, logger)
    except ValueError as exc:
        logger.error('%s', exc)
        return 1
    for key, reason in dropped:
        excluded.append((by_key[key], reason))

    included = [by_key[key] for key in panel.columns]
    names = [m.name for m in included]
    values_sek = np.array([m.market_value_sek for m in included])
    tickers = ['%s:%s' % resolved[m.key] if resolved[m.key][0] == 'avanza' else resolved[m.key][1]
               for m in included]
    total_sek = float(values_sek.sum())
    current_weights = values_sek / total_sek

    excluded_value = sum(h.market_value_sek for h, _ in excluded)
    if excluded_value > 0:
        share = excluded_value / (total_sek + excluded_value)
        logger.warning('Optimizing over %s (%.0f%% of portfolio); %s excluded',
                       _sek(total_sek), 100 * (1 - share), _sek(excluded_value))

    returns = to_returns(panel)
    result = optimize(names, returns.to_numpy(), current_weights,
                      rf=args.risk_free, max_weight=args.max_weight)

    print_results(result, names, tickers, values_sek, excluded, total_sek)

    report = render_report(
        result, names, tickers, values_sek, excluded, total_sek,
        rf=args.risk_free,
        window_start=str(panel.index[0].date()),
        window_end=str(panel.index[-1].date()),
        n_days=len(panel),
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M'),
    )
    output = Path(args.output)
    output.write_text(report, encoding='utf-8')
    logger.info('Report written to %s', output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
