import requests
from typing import Dict, Any, List
from utils.config import YAHOO_API_BASE_URL, YAHOO_API_PARAMS


def get_nested(dict_: Dict, *keys: str, default=None) -> Any:
    # Recursive helper function for traversing nested dictionaries
    if not isinstance(dict_, dict):
        return default
    elem = dict_.get(keys[0], default)
    if len(keys) == 1:
        return elem
    return get_nested(elem, *keys[1:], default=default)


def make_yahoo_request(yahoo_ticker: str, params: Dict) -> Dict:
    response: Dict = requests.get(YAHOO_API_BASE_URL.format(yahoo_ticker), params=params).json()
    payload: Dict = get_nested(response, 'quoteSummary', 'result')[0]
    return payload


def fetch_yahoo_data(yahoo_ticker: str, modules: str) -> Dict:
    params: Dict = YAHOO_API_PARAMS.copy()
    params['modules'] = modules
    response = make_yahoo_request(yahoo_ticker, params)
    return response


def union_of_list_elements(*lists: List[Any]) -> List[Any]:
    lists_appended: List[Any] = sum(lists, [])
    return list(set(lists_appended))
