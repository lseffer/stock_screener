"""Fetch and align daily price history for resolved holdings.

Yahoo-resolved instruments come via yfinance; Avanza-resolved funds via the
public NAV chart endpoint. The panel is aligned per align_and_clean(): assets
whose history is too short to keep a useful common window are dropped (not the
window truncated), small gaps are forward-filled (fund NAV lags, holiday
mismatches), and the run aborts only if too little usable data remains.

Returns are computed on native-currency series; under the static-FX design a
currency conversion is a scalar multiply and does not change returns.
"""
import time
from typing import Dict, List, Tuple

import pandas as pd

from portfolio_opt import avanza_public
from portfolio_opt.resolve import Resolution
from utils.config import bind_ticker

MIN_ROWS_ABORT = 60
FFILL_LIMIT = 5


def fetch_history(resolved: Dict[str, Resolution], years: int, log,
                  ) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """Fetch daily closes per ISIN. Returns (wide frame keyed by ISIN, failures)."""
    import yfinance as yf

    series: Dict[str, pd.Series] = {}
    failures: List[Tuple[str, str]] = []
    for isin, (source, identifier) in resolved.items():
        tlog = bind_ticker(log, '%s:%s' % (source, identifier))
        try:
            if source == 'yahoo':
                history = yf.Ticker(identifier).history(
                    period='%dy' % years, interval='1d', auto_adjust=True
                )
                closes = history['Close'].dropna() if history is not None and not history.empty else None
                if closes is not None and not closes.empty:
                    closes.index = pd.DatetimeIndex(closes.index.tz_localize(None)).normalize()
                    series[isin] = closes[~closes.index.duplicated(keep='last')]
                else:
                    failures.append((isin, 'yahoo returned no price history'))
                    tlog.warning('No price history returned')
            elif source == 'avanza':
                nav = avanza_public.fetch_nav_history(identifier, years, tlog)
                if nav:
                    idx = pd.DatetimeIndex(pd.to_datetime(sorted(nav)))
                    series[isin] = pd.Series([nav[d.date()] for d in idx], index=idx)
                else:
                    failures.append((isin, 'avanza returned no NAV history'))
                    tlog.warning('No NAV history returned')
            else:
                failures.append((isin, 'unknown price source %s' % source))
        except Exception:
            tlog.exception('Price fetch failed')
            failures.append((isin, 'price fetch failed'))
        time.sleep(0.1)

    prices = pd.DataFrame(series).sort_index() if series else pd.DataFrame()
    return prices, failures


def align_and_clean(prices: pd.DataFrame, min_days: int, log,
                    ) -> Tuple[pd.DataFrame, List[Tuple[str, str]]]:
    """Align the price panel to a common daily window. Returns (panel, dropped)."""
    dropped: List[Tuple[str, str]] = []
    panel = prices.dropna(how='all').sort_index()

    # Drop short-history assets that would shrink the common window below
    # min_days, starting with the shortest, instead of truncating everyone.
    while len(panel.columns) > 1:
        first_valid = {col: panel[col].first_valid_index() for col in panel.columns}
        usable = {col: idx for col, idx in first_valid.items() if idx is not None}
        for col in set(panel.columns) - set(usable):
            dropped.append((col, 'no usable price data'))
            panel = panel.drop(columns=col)
        if not usable or len(panel.columns) <= 1:
            break
        window_rows = len(panel.loc[max(usable.values()):])
        if window_rows >= min_days:
            break
        shortest = max(usable, key=lambda col: usable[col])
        remaining = {c: i for c, i in usable.items() if c != shortest}
        if not remaining:
            break
        rows_without = len(panel.loc[max(remaining.values()):])
        if rows_without <= window_rows:
            break  # dropping it doesn't help; keep it
        log.warning(
            'Dropping %s: only %d common trading days with it included (< %d)',
            shortest, window_rows, min_days,
        )
        dropped.append((shortest, 'price history too short'))
        panel = panel.drop(columns=shortest)

    if panel.empty or len(panel.columns) == 0:
        raise ValueError('No usable price history for any holding')

    start = max(panel[col].first_valid_index() for col in panel.columns)
    panel = panel.loc[start:]
    panel = panel.ffill(limit=FFILL_LIMIT).dropna()

    if len(panel) < min_days:
        log.warning('Only %d common trading days available (wanted >= %d); '
                    'estimates will be noisy', len(panel), min_days)
    if len(panel) < MIN_ROWS_ABORT:
        raise ValueError(
            'Only %d common trading days across holdings; refusing to optimize '
            'on so little data' % len(panel)
        )
    if len(panel.columns) < 2:
        raise ValueError('Need at least 2 holdings with price history to optimize')
    return panel, dropped


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple daily returns; simple (not log) because portfolio weights
    aggregate linearly across assets."""
    return prices.pct_change().dropna()
