"""Unauthenticated access to avanza.se public endpoints.

These are the same endpoints the avanza.se website calls without a login:
search (ISIN/name -> orderbook id) and the fund-guide chart (orderbook id ->
daily NAV/development series). They are unofficial and change over time, so
several endpoint variants are tried in order and all parsing is defensive:
any failure returns None/{} and the instrument is simply excluded from the
optimization rather than crashing the run.

No credentials are used anywhere.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional

import requests

# Search endpoint variants, tried in order. Shapes seen in the wild:
#   _cqbe global-search:  {"resultGroups": [{"instrumentType": "FUND",
#                          "hits": [{"link": {"orderbookId": "325406", ...}}]}]}
#   _api filtered-search (POST): {"hits": [{"orderbookId": ..., ...}]}
#   _mobile market search: {"hits": [{"instrumentType": "FUND",
#                          "topHits": [{"id": "325406", ...}]}]}
SEARCH_GET_URLS = [
    'https://www.avanza.se/_cqbe/search/global-search/global-search-template',
    'https://www.avanza.se/_api/search/filtered-search',
]
SEARCH_POST_URL = 'https://www.avanza.se/_api/search/filtered-search'
SEARCH_MOBILE_URL = 'https://www.avanza.se/_mobile/market/search/FUND'

FUND_CHART_URLS = [
    'https://www.avanza.se/_api/fund-guide/chart/{orderbook_id}/{start}/{end}?raw=true',
    'https://www.avanza.se/_api/fund-guide/chart/{orderbook_id}/{start}/{end}',
    'https://www.avanza.se/_cqbe/fund/chart/{orderbook_id}/{start}/{end}',
]

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/126.0 Safari/537.36'
    ),
    'Accept': 'application/json',
}

TIMEOUT = 20


def _get_json(url: str, log, params=None):
    try:
        response = requests.get(url, params=params, headers=_HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception:
        log.debug('GET %s failed', url, exc_info=True)
        return None


def search_orderbook_id(query: str, log) -> Optional[str]:
    """Search avanza.se for ``query`` (ISIN or name); return the first orderbook
    id, preferring FUND hits. Tries several endpoint variants."""
    payloads = []
    for url in SEARCH_GET_URLS:
        payloads.append(_get_json(url, log, params={'query': query}))
    try:
        response = requests.post(
            SEARCH_POST_URL,
            json={'query': query, 'pagination': {'from': 0, 'size': 10}},
            headers=_HEADERS, timeout=TIMEOUT,
        )
        response.raise_for_status()
        payloads.append(response.json())
    except Exception:
        log.debug('POST %s failed', SEARCH_POST_URL, exc_info=True)
    payloads.append(_get_json(SEARCH_MOBILE_URL, log,
                              params={'query': query, 'maxResults': 10}))

    for payload in payloads:
        orderbook_id = _extract_orderbook_id(payload)
        if orderbook_id:
            return orderbook_id
    log.warning('Avanza search found nothing for %r on any endpoint', query)
    return None


def _extract_orderbook_id(payload) -> Optional[str]:
    """Pull the first orderbook id out of a search response, whatever its shape.
    FUND hits win over other instrument types."""
    if not isinstance(payload, dict):
        return None
    fund_ids: List[str] = []
    other_ids: List[str] = []

    def visit(node, in_fund_group):
        if isinstance(node, dict):
            group_type = str(node.get('instrumentType', '')).upper()
            is_fund = in_fund_group or group_type == 'FUND'
            for key in ('orderbookId', 'orderBookId'):
                if node.get(key) is not None:
                    (fund_ids if is_fund else other_ids).append(str(node[key]))
            # _mobile shape: fund hits carry the id under topHits[].id
            for hit in node.get('topHits') or []:
                if isinstance(hit, dict) and hit.get('id') is not None:
                    (fund_ids if is_fund else other_ids).append(str(hit['id']))
            for value in node.values():
                visit(value, is_fund)
        elif isinstance(node, list):
            for item in node:
                visit(item, in_fund_group)

    visit(payload, False)
    if fund_ids:
        return fund_ids[0]
    return other_ids[0] if other_ids else None


def fetch_nav_history(orderbook_id: str, years: float, log) -> Dict[date, float]:
    """Daily price-relative series for a fund as {date: value}. The scale is
    arbitrary (NAV, or a rebased index when the endpoint returns percent
    development) — only day-over-day returns matter downstream.
    Empty dict on failure."""
    end = date.today()
    start = end - timedelta(days=int(years * 365.25) + 7)
    for template in FUND_CHART_URLS:
        url = template.format(orderbook_id=orderbook_id, start=start.isoformat(),
                              end=end.isoformat())
        payload = _get_json(url, log)
        series = parse_nav_payload(payload)
        if series:
            return series
    log.warning('Avanza NAV history unavailable for orderbook %s on any endpoint',
                orderbook_id)
    return {}


def parse_nav_payload(payload) -> Dict[date, float]:
    """Parse a fund-guide chart response into {date: value}, tolerating both the
    {"dataSerie": [{"x": epoch_ms, "y": value}]} and {"data": [...]} shapes.

    The y values are either a NAV or a percent-development series rebased to 0
    at the window start (the fund-guide chart does the latter). Development is
    detected by a first value of ~0 or any negative value, and converted to a
    price-relative index (1 + y/100) so downstream returns are correct either
    way."""
    if not isinstance(payload, dict):
        return {}
    series = payload.get('dataSerie') or payload.get('dataSeries') or payload.get('data') or []
    points = []
    for item in series:
        if not isinstance(item, dict):
            continue
        x, y = item.get('x'), item.get('y')
        if x is None or y is None:
            continue
        try:
            points.append((date.fromtimestamp(float(x) / 1000.0), float(y)))
        except (ValueError, OSError, OverflowError):
            continue
    if not points:
        return {}
    points.sort()
    values = [y for _, y in points]
    is_development = abs(values[0]) < 1e-9 or min(values) < 0
    if is_development:
        result = {}
        for day, y in points:
            rebased = 1.0 + y / 100.0
            if rebased > 0:
                result[day] = rebased
        return result
    return dict(points)
