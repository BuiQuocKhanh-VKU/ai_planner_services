import copy
import re
from typing import Any, Dict, List, Optional

from app.schemas.planner_schemas import ensure_items_shape


TIME_RANGE_MAP = {
    "sáng": {"range_hint": "morning", "start_hour": 8, "end_hour": 11},
    "trưa": {"range_hint": "noon", "start_hour": 11, "end_hour": 13},
    "chiều": {"range_hint": "afternoon", "start_hour": 13, "end_hour": 17},
    "tối": {"range_hint": "evening", "start_hour": 18, "end_hour": 22},
    "đêm": {"range_hint": "night", "start_hour": 22, "end_hour": 24},
    "mai sáng": {"range_hint": "next_day_morning", "start_hour": 8, "end_hour": 11},
    "mai chiều": {"range_hint": "next_day_afternoon", "start_hour": 13, "end_hour": 17},
    "mai tối": {"range_hint": "next_day_evening", "start_hour": 18, "end_hour": 22},
}

PRIORITY_MAP = {
    "urgent": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()) if text else ""


def _ensure_temporal_meta(item: Dict[str, Any]) -> None:
    item.setdefault("parsed_time", None)
    item.setdefault("parsed_duration", None)
    item.setdefault("parsed_deadline", None)
    item.setdefault("temporal_flags", [])
    item.setdefault("temporal_notes", [])
    item.setdefault("needs_time_confirmation", False)


def _flag(item: Dict[str, Any], flag: str) -> None:
    _ensure_temporal_meta(item)
    if flag not in item["temporal_flags"]:
        item["temporal_flags"].append(flag)


def _note(item: Dict[str, Any], note: str) -> None:
    _ensure_temporal_meta(item)
    item["temporal_notes"].append(note)


def _confirm(item: Dict[str, Any], note: str) -> None:
    _ensure_temporal_meta(item)
    item["needs_time_confirmation"] = True
    item["temporal_notes"].append(note)


def _parse_clock_text(text: Optional[str]) -> Optional[Dict[str, Any]]:
    t = _norm(text)
    if not t:
        return None

    # 14:30
    m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        return {
            "time_type": "clock_time",
            "hour": hour,
            "minute": minute,
            "text": text,
            "is_ambiguous_meridiem": hour <= 12,
        }

    # 3h / 3 giờ / 15h
    m = re.search(r"\b(\d{1,2})\s*(h|giờ)\b", t)
    if m:
        hour = int(m.group(1))
        return {
            "time_type": "clock_time",
            "hour": hour,
            "minute": 0,
            "text": text,
            "is_ambiguous_meridiem": hour <= 12,
        }

    return None


def _parse_range_hint(text: Optional[str]) -> Optional[Dict[str, Any]]:
    t = _norm(text)
    if not t:
        return None

    if t in TIME_RANGE_MAP:
        data = TIME_RANGE_MAP[t]
        return {
            "time_type": "range_hint",
            "range_hint": data["range_hint"],
            "approx_start_hour": data["start_hour"],
            "approx_end_hour": data["end_hour"],
            "text": text,
        }

    return None


def _parse_time_text(text: Optional[str]) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    exact = _parse_clock_text(text)
    if exact:
        return exact

    hinted = _parse_range_hint(text)
    if hinted:
        return hinted

    return {
        "time_type": "unparsed_time_text",
        "text": text,
    }


def _parse_duration_text(text: Optional[str]) -> Optional[Dict[str, Any]]:
    t = _norm(text)
    if not t:
        return None

    # 2 tiếng
    m = re.search(r"\b(\d{1,2})\s*tiếng\b", t)
    if m:
        hours = int(m.group(1))
        return {
            "duration_type": "duration",
            "minutes": hours * 60,
            "text": text,
        }

    # 30 phút
    m = re.search(r"\b(\d{1,3})\s*phút\b", t)
    if m:
        minutes = int(m.group(1))
        return {
            "duration_type": "duration",
            "minutes": minutes,
            "text": text,
        }

    # 1 giờ rưỡi
    m = re.search(r"\b(\d{1,2})\s*giờ\s*rưỡi\b", t)
    if m:
        hours = int(m.group(1))
        return {
            "duration_type": "duration",
            "minutes": hours * 60 + 30,
            "text": text,
        }

    return {
        "duration_type": "unparsed_duration_text",
        "text": text,
    }


def _parse_deadline_text(text: Optional[str]) -> Optional[Dict[str, Any]]:
    t = _norm(text)
    if not t:
        return None

    # trước 5h / trước 17:00
    m = re.search(r"\btrước\s+(\d{1,2})(?::(\d{2}))?\s*(h|giờ)?\b", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        return {
            "deadline_type": "before_time",
            "hour": hour,
            "minute": minute,
            "text": text,
            "is_ambiguous_meridiem": hour <= 12,
        }

    # deadline mềm kiểu "hôm nay", "ngày mai"
    if "hôm nay" in t:
        return {
            "deadline_type": "relative_day",
            "day_hint": "today",
            "text": text,
        }

    if "ngày mai" in t or "mai" in t:
        return {
            "deadline_type": "relative_day",
            "day_hint": "tomorrow",
            "text": text,
        }

    return {
        "deadline_type": "unparsed_deadline_text",
        "text": text,
    }


def _post_check_time(item: Dict[str, Any]) -> None:
    parsed_time = item.get("parsed_time")
    parsed_duration = item.get("parsed_duration")
    parsed_deadline = item.get("parsed_deadline")

    if parsed_time and parsed_time.get("time_type") == "clock_time":
        if parsed_time.get("is_ambiguous_meridiem"):
            _flag(item, "ambiguous_clock_time")
            _confirm(item, f"time '{item.get('time_text')}' chưa rõ sáng hay chiều")

    if parsed_deadline and parsed_deadline.get("deadline_type") == "before_time":
        if parsed_deadline.get("is_ambiguous_meridiem"):
            _flag(item, "ambiguous_deadline_time")
            _confirm(item, f"deadline '{item.get('deadline_text')}' chưa rõ sáng hay chiều")

    if parsed_time and parsed_duration:
        if parsed_time.get("time_type") == "clock_time" and parsed_duration.get("duration_type") == "duration":
            _flag(item, "has_start_time_and_duration")
            _note(item, "item có cả giờ bắt đầu và thời lượng, phù hợp để scheduling tiếp")

    if parsed_time and parsed_time.get("time_type") == "range_hint":
        _flag(item, "vague_time_range")
        _confirm(item, f"time_text '{item.get('time_text')}' còn là khoảng thời gian, chưa phải giờ cụ thể")


def _add_temporal_summary(item: Dict[str, Any]) -> None:
    parsed_time = item.get("parsed_time")
    parsed_duration = item.get("parsed_duration")
    parsed_deadline = item.get("parsed_deadline")

    summary = {}

    if parsed_time:
        summary["has_time"] = True
        summary["time_type"] = parsed_time.get("time_type")
    else:
        summary["has_time"] = False

    if parsed_duration:
        summary["has_duration"] = True
        summary["duration_minutes"] = parsed_duration.get("minutes")
    else:
        summary["has_duration"] = False

    if parsed_deadline:
        summary["has_deadline"] = True
        summary["deadline_type"] = parsed_deadline.get("deadline_type")
    else:
        summary["has_deadline"] = False

    item["temporal_summary"] = summary


def temporal_reason(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      semantic_output data

    Output:
      {
        "data": {...},
        "issues": [...]
      }
    """
    result = copy.deepcopy(data)
    issues: List[str] = []

    items = ensure_items_shape(result.get("items", []))
    processed: List[Dict[str, Any]] = []

    for idx, item in enumerate(items):
        _ensure_temporal_meta(item)

        item["parsed_time"] = _parse_time_text(item.get("time_text"))
        item["parsed_duration"] = _parse_duration_text(item.get("duration_text"))
        item["parsed_deadline"] = _parse_deadline_text(item.get("deadline_text"))

        _post_check_time(item)
        _add_temporal_summary(item)

        if item["parsed_time"] and item["parsed_time"].get("time_type") == "unparsed_time_text":
            issues.append(f"unparsed_time_text:item_{idx}:{item.get('time_text')}")

        if item["parsed_duration"] and item["parsed_duration"].get("duration_type") == "unparsed_duration_text":
            issues.append(f"unparsed_duration_text:item_{idx}:{item.get('duration_text')}")

        if item["parsed_deadline"] and item["parsed_deadline"].get("deadline_type") == "unparsed_deadline_text":
            issues.append(f"unparsed_deadline_text:item_{idx}:{item.get('deadline_text')}")

        processed.append(item)

    result["items"] = processed
    return {
        "data": result,
        "issues": issues,
    }