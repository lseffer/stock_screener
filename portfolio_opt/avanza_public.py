"""Unauthenticated access to avanza.se public endpoints.

These are the same endpoints the avanza.se website calls without a login:
a search endpoint (ISIN/name -> orderbook id) and a fund-guide chart endpoint
(orderbook id -> daily NAV series). They are unofficial and may change shape,
so all parsing is defensive: any failure returns None/{} and the instrument is
simply excluded from the optimization rather than crashing the run.

No credentials are used anywhere.
"""
from datetime import date, timedelta
from typing import Dict, Optional

import requests

SEARCH_URL = 'https://www.avanza.se/_api/search/filtered-search'
FUND_CHART_URL = 'https://www.avanza.se/_api/fund-guide/chart/{orderbook_id}/{start}/{end}'

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/126.0 Safari/537.36'
    ),
    'Accept': 'application/json',
}

TIMEOUT = 20


def search_orderbook_id(query: str, log) -> Optional[str]:
    """Search avanza.se for ``query`` (ISIN or name); return the first orderbook id."""
    try:
        response = requests.get(
            SEARCH_URL, params={'query': query}, headers=_HEADERS, timeout=TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        log.warning('Avanza search failed for %s', query, exc_info=True)
        return None
    return _extract_orderbook_id(payload)


def _extract_orderbook_id(payload) -> Optional[str]:
    """Pull the first orderbook id out of a search response, whatever its shape."""
    if not isinstance(payload, dict):
        return None
    hit_lists = []
    # Known shapes: {"hits": [...]} and {"resultGroups": [{"hits": [...]}]}
    if isinstance(payload.get('hits'), list):
        hit_lists.append(payload['hits'])
    for group in payload.get('resultGroups', []) or []:
        if isinstance(group, dict) and isinstance(group.get('hits'), list):
            hit_lists.append(group['hits'])
    for hits in hit_lists:
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            for key in ('orderbookId', 'orderBookId', 'id'):
                value = hit.get(key) or (hit.get('link') or {}).get(key)
                if value is not None:
                    return str(value)
    return None


def fetch_nav_history(orderbook_id: str, years: int, log) -> Dict[date, float]:
    """Daily NAV series for a fund as {date: nav}. Empty dict on any failure."""
    end = date.today()
    start = end - timedelta(days=int(years * 365.25) + 7)
    url = FUND_CHART_URL.format(orderbook_id=orderbook_id, start=start.isoformat(), end=end.isoformat())
    try:
        response = requests.get(url, headers=_HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        log.warning('Avanza NAV fetch failed for orderbook %s', orderbook_id, exc_info=True)
        return {}
    return parse_nav_payload(payload)


def parse_nav_payload(payload) -> Dict[date, float]:
    """Parse a fund-guide chart response into {date: nav}, tolerating both the
    {"dataSerie": [{"x": epoch_ms, "y": nav}]} and {"data": [...]} shapes."""
    if not isinstance(payload, dict):
        return {}
    series = payload.get('dataSerie') or payload.get('dataSeries') or payload.get('data') or []
    result: Dict[date, float] = {}
    for item in series:
        if not isinstance(item, dict):
            continue
        x, y = item.get('x'), item.get('y')
        if x is None or y is None:
            continue
        try:
            result[date.fromtimestamp(float(x) / 1000.0)] = float(y)
        except (ValueError, OSError, OverflowError):
            continue
    return result
