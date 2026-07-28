"""Resolve holdings (by ISIN) to a price source.

A resolution is a (source, identifier) tuple: ('yahoo', 'ERIC-B.ST') or
('avanza', '<orderbookId>'). Precedence: ticker_overrides.csv, then the local
resolution cache, then auto-resolution (Yahoo search by ISIN, then avanza.se
public search — the latter covers Avanza's own funds which Yahoo often lacks).

Negative results are never cached, so a transient search failure is retried on
the next run. Unresolved holdings are excluded from the optimization and
reported; add them to portfolio/ticker_overrides.csv to pin them manually.
"""
import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from portfolio_opt import avanza_public
from portfolio_opt.holdings import MergedHolding, holding_key
from utils.config import bind_ticker

Resolution = Tuple[str, str]  # (source, identifier)

OVERRIDES_FILENAME = 'ticker_overrides.csv'
CACHE_FILENAME = '.ticker_cache.json'

# Preferred Yahoo exchange suffix per ISIN country prefix.
COUNTRY_SUFFIX = {'SE': '.ST', 'DK': '.CO', 'FI': '.HE', 'NO': '.OL'}

EXCLUDED = ('excluded', '')  # sentinel for deliberate exclusion via empty override


def parse_override_value(value: str) -> Optional[Resolution]:
    """'' -> None (exclude); 'avanza:1234' -> ('avanza', '1234'); else yahoo ticker."""
    value = (value or '').strip()
    if not value:
        return None
    if value.lower().startswith('avanza:'):
        return ('avanza', value.split(':', 1)[1].strip())
    return ('yahoo', value)


def load_overrides(portfolio_dir: Path, log) -> Dict[str, Optional[Resolution]]:
    """Overrides keyed by holding key. The first CSV column may be an ISIN or,
    for name-only holdings, the fund name exactly as it appears in the export."""
    path = portfolio_dir / OVERRIDES_FILENAME
    if not path.exists():
        return {}
    overrides: Dict[str, Optional[Resolution]] = {}
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            identifier = (row.get('isin') or row.get('name') or '').strip()
            if not identifier:
                continue
            key = holding_key(identifier, identifier)
            overrides[key] = parse_override_value(row.get('ticker') or row.get('yahoo_ticker') or '')
    if overrides:
        log.info('Loaded %d ticker override(s) from %s', len(overrides), path)
    return overrides


class ResolutionCache:
    def __init__(self, portfolio_dir: Path):
        self.path = portfolio_dir / CACHE_FILENAME
        self._data: Dict[str, Dict[str, str]] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (ValueError, OSError):
                self._data = {}

    def get(self, isin: str) -> Optional[Resolution]:
        entry = self._data.get(isin)
        if entry and entry.get('source') and entry.get('id'):
            return (entry['source'], entry['id'])
        return None

    def put(self, isin: str, resolution: Resolution) -> None:
        self._data[isin] = {'source': resolution[0], 'id': resolution[1]}

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2, sort_keys=True))


def _yahoo_search(query: str, preferred_suffix: Optional[str], log) -> Optional[str]:
    import yfinance as yf

    try:
        quotes = yf.Search(query, max_results=5).quotes or []
    except Exception:
        log.warning('Yahoo search failed for %s', query, exc_info=True)
        quotes = []
    symbols = [q.get('symbol') for q in quotes if isinstance(q, dict) and q.get('symbol')]
    if symbols:
        if preferred_suffix:
            for symbol in symbols:
                if symbol.endswith(preferred_suffix):
                    return symbol
        return symbols[0]
    return None


def _yahoo_resolve_isin(isin: str, log) -> Optional[str]:
    import yfinance as yf

    symbol = _yahoo_search(isin, COUNTRY_SUFFIX.get(isin[:2]), log)
    if symbol:
        return symbol

    if hasattr(yf, 'Lookup'):
        try:
            lookup = yf.Lookup(isin).all
            if lookup is not None and len(lookup) > 0:
                return str(lookup.index[0])
        except Exception:
            log.debug('Yahoo lookup failed for %s', isin, exc_info=True)

    try:
        history = yf.Ticker(isin).history(period='5d', auto_adjust=True)
        if history is not None and not history.empty:
            return isin
    except Exception:
        log.debug('Yahoo direct-ISIN probe failed for %s', isin, exc_info=True)
    return None


def auto_resolve(isin: str, name: str, log) -> Optional[Resolution]:
    """Resolve by ISIN when there is one; otherwise by name.

    Name-only holdings try avanza.se first: fund names like "Avanza Zero" or
    "Avanza 100" are Avanza's own products and their search matches them
    exactly, while Yahoo's name search is noisier."""
    if isin:
        symbol = _yahoo_resolve_isin(isin, log)
        if symbol:
            return ('yahoo', symbol)
        orderbook_id = avanza_public.search_orderbook_id(isin, log)
        if orderbook_id is None and name:
            orderbook_id = avanza_public.search_orderbook_id(name, log)
        if orderbook_id:
            return ('avanza', orderbook_id)
        return None

    if not name:
        return None
    orderbook_id = avanza_public.search_orderbook_id(name, log)
    if orderbook_id:
        return ('avanza', orderbook_id)
    symbol = _yahoo_search(name, None, log)
    if symbol:
        return ('yahoo', symbol)
    return None


def resolve_all(merged: List[MergedHolding], overrides: Dict[str, Optional[Resolution]],
                cache: ResolutionCache, log, resolver=auto_resolve,
                ) -> Tuple[Dict[str, Resolution], List[Tuple[MergedHolding, str]]]:
    """Returns ({holding key: resolution}, [(holding, reason) for excluded holdings]).

    Holding keys are ISINs, or normalized-name keys for holdings without one."""
    resolved: Dict[str, Resolution] = {}
    excluded: List[Tuple[MergedHolding, str]] = []
    for holding in merged:
        key = holding.key
        tlog = bind_ticker(log, holding.isin or holding.name)
        if key in overrides:
            override = overrides[key]
            if override is None:
                excluded.append((holding, 'excluded via ticker_overrides.csv'))
            else:
                resolved[key] = override
            continue
        cached = cache.get(key)
        if cached is not None:
            tlog.info('Resolved from cache: %s:%s', *cached)
            resolved[key] = cached
            continue
        resolution = resolver(holding.isin, holding.name, tlog)
        if resolution is None:
            tlog.warning('Could not resolve %s to a price source',
                         '%s (%s)' % (holding.isin, holding.name) if holding.isin else holding.name)
            excluded.append((holding, 'no price source found'))
        else:
            tlog.info('Auto-resolved to %s:%s', *resolution)
            resolved[key] = resolution
            cache.put(key, resolution)
        time.sleep(0.1)
    cache.save()
    if excluded:
        log.warning(
            'Excluded %d holding(s) with no price source. Pin them manually in '
            '%s (first column is the ISIN, or the holding name for rows without '
            'one; ticker is a Yahoo ticker or avanza:<orderbookId>).',
            len(excluded), OVERRIDES_FILENAME,
        )
    return resolved, excluded
