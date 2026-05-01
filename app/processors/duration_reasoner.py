import copy
import re
from typing import Any, Dict, List, Optional


DEFAULT_DURATION_BY_TYPE = {
    "task": 60,
    "study": 60,
    "work": 60,
    "event": 60,
    "meeting": 60,
    "habit": 30,
    "personal": 30,
    "reminder": 15,
    "other": 30,
}


TITLE_DURATION_RULES = [
    {
        "keywords": ["uống thuốc", "nhắc", "remind", "gọi điện", "call"],
        "minutes": 15,
        "source": "default_by_short_action_title",
    },
    {
        "keywords": ["học", "học bài", "ôn", "ôn thi", "làm bài", "bài tập", "làm việc"],
        "minutes": 60,
        "source": "default_by_study_or_work_title",
    },
    {
        "keywords": ["tập đàn", "tập gym", "chạy bộ", "thể dục", "đọc sách"],
        "minutes": 30,
        "source": "default_by_habit_title",
    },
    {
        "keywords": ["đi ngủ", "ngủ"],
        "minutes": 15,
        "source": "default_by_sleep_anchor_title",
    },
]


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm(value: Any) -> str:
    text = _safe_str(value)
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.lower()).strip()


def _get_explicit_duration_minutes(item: Dict[str, Any]) -> Optional[int]:
    parsed_duration = item.get("parsed_duration")

    if not isinstance(parsed_duration, dict):
        return None

    if parsed_duration.get("duration_type") != "duration":
        return None

    minutes = parsed_duration.get("minutes")

    if not isinstance(minutes, int):
        return None

    if minutes <= 0:
        return None

    return minutes


def _infer_default_duration(item: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(item.get("title"))
    item_type = _norm(item.get("item_type")) or "other"

    for rule in TITLE_DURATION_RULES:
        for keyword in rule["keywords"]:
            if keyword in title:
                return {
                    "duration_minutes": rule["minutes"],
                    "source": rule["source"],
                }

    minutes = DEFAULT_DURATION_BY_TYPE.get(item_type, DEFAULT_DURATION_BY_TYPE["other"])

    return {
        "duration_minutes": minutes,
        "source": "default_by_item_type",
    }


def _build_explicit_duration_resolution(minutes: int) -> Dict[str, Any]:
    return {
        "duration_minutes": minutes,
        "source": "explicit_duration_text",
        "is_default": False,
        "is_flexible": False,
        "can_expand": False,
        "can_split": False,
        "min_minutes": minutes,
        "max_minutes": minutes,
    }


def _build_default_duration_resolution(item: Dict[str, Any]) -> Dict[str, Any]:
    inferred = _infer_default_duration(item)
    minutes = inferred["duration_minutes"]

    return {
        "duration_minutes": minutes,
        "source": inferred["source"],
        "is_default": True,
        "is_flexible": True,
        "can_expand": False,
        "can_split": False,
        "min_minutes": max(15, min(minutes, 30)),
        "max_minutes": minutes,
    }


def _should_apply_default_duration(item: Dict[str, Any]) -> bool:
    parsed_time = item.get("parsed_time")

    if not isinstance(parsed_time, dict):
        return False

    if parsed_time.get("time_type") != "clock_time":
        return False

    return True


def duration_reason(data: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(data)
    issues: List[str] = []

    items = result.get("items", [])

    if not isinstance(items, list):
        result["items"] = []
        return {
            "data": result,
            "issues": ["duration_items_not_list_reset"],
        }

    processed_items: List[Dict[str, Any]] = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"duration_invalid_item_skipped:{idx}")
            continue

        explicit_minutes = _get_explicit_duration_minutes(item)

        if explicit_minutes is not None:
            item["duration_resolution"] = _build_explicit_duration_resolution(explicit_minutes)
        elif _should_apply_default_duration(item):
            item["duration_resolution"] = _build_default_duration_resolution(item)
            issues.append(f"default_duration_applied:item_{idx}:{item.get('title')}")
        else:
            item["duration_resolution"] = None
            issues.append(f"no_duration_resolution:item_{idx}:{item.get('title')}")

        processed_items.append(item)

    result["items"] = processed_items

    return {
        "data": result,
        "issues": issues,
    }