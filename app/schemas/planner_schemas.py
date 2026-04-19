from typing import Dict, Any, List

#field chuẩn, tránh hardcode lung tung.
DEFAULT_ITEM = {
    "item_type": None,
    "title": None,
    "time_text": None,
    "duration_text": None,
    "deadline_text": None,
    "priority": None,
    "person": None,
    "location": None,
    "constraint_text": None,
    "source_text": None,
}

DEFAULT_TEMPORAL_FIELDS = {
    "parsed_time": None,
    "parsed_duration": None,
    "parsed_deadline": None,
    "temporal_flags": [],
    "temporal_notes": [],
    "needs_time_confirmation": False,
}


def ensure_item_shape(item: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(DEFAULT_ITEM)
    out.update(item or {})

    temporal = dict(DEFAULT_TEMPORAL_FIELDS)
    for k, v in temporal.items():
        out.setdefault(k, v if not isinstance(v, list) else list(v))

    return out


def ensure_items_shape(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [ensure_item_shape(x) for x in items]