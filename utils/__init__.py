from typing import Any, Dict, List


def get_nested(dict_: Dict, *keys: str, default=None) -> Any:
    if not isinstance(dict_, dict):
        return default
    elem = dict_.get(keys[0], default)
    if len(keys) == 1:
        return elem
    return get_nested(elem, *keys[1:], default=default)


def union_of_list_elements(*lists: List[Any]) -> List[Any]:
    lists_appended: List[Any] = sum(lists, [])
    return list(set(lists_appended))
