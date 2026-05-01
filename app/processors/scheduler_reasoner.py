import copy
from typing import Any, Dict, List, Optional


DAY_MINUTES = 24 * 60


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    return None


def _minutes_to_time_obj(total_minutes: int) -> Dict[str, Any]:
    """
    Đổi phút trong ngày về hour/minute.
    Nếu vượt qua 24h thì ghi thêm day_offset.
    """
    day_offset = total_minutes // DAY_MINUTES
    minutes_in_day = total_minutes % DAY_MINUTES

    hour = minutes_in_day // 60
    minute = minutes_in_day % 60

    return {
        "hour": hour,
        "minute": minute,
        "day_offset": day_offset,
        "text": f"{hour:02d}:{minute:02d}",
    }


def _clock_time_to_minutes(parsed_time: Any) -> Optional[int]:
    if not isinstance(parsed_time, dict):
        return None

    if parsed_time.get("time_type") != "clock_time":
        return None

    hour = _safe_int(parsed_time.get("hour"))
    minute = parsed_time.get("minute", 0)

    if hour is None:
        return None

    if not isinstance(minute, int):
        minute = 0

    if hour < 0 or hour > 23:
        return None

    if minute < 0 or minute > 59:
        minute = 0

    return hour * 60 + minute


def _duration_to_minutes(parsed_duration: Any, item: Optional[Dict[str, Any]] = None) -> Optional[int]:
    if isinstance(parsed_duration, dict):
        if parsed_duration.get("duration_type") == "duration":
            minutes = parsed_duration.get("minutes")

            if isinstance(minutes, int) and minutes > 0:
                return minutes

    if isinstance(item, dict):
        duration_resolution = item.get("duration_resolution")

        if isinstance(duration_resolution, dict):
            minutes = duration_resolution.get("duration_minutes")

            if isinstance(minutes, int) and minutes > 0:
                return minutes

    return None


def _build_exact_time_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    parsed_time = item.get("parsed_time")
    parsed_duration = item.get("parsed_duration")

    start_minutes = _clock_time_to_minutes(parsed_time)

    if start_minutes is None:
        return None

    duration_minutes = _duration_to_minutes(parsed_duration, item)

    start_obj = _minutes_to_time_obj(start_minutes)

    candidate = {
        "candidate_type": "exact_start_time",
        "start": start_obj,
        "end": None,
        "duration_minutes": duration_minutes,
        "is_ambiguous_meridiem": bool(parsed_time.get("is_ambiguous_meridiem")),
        "needs_confirmation": False,
        "confidence": "medium",
        "reason": None,
    }

    if duration_minutes:
        end_minutes = start_minutes + duration_minutes
        candidate["end"] = _minutes_to_time_obj(end_minutes)
        candidate["candidate_type"] = "exact_start_end_time"

    if candidate["is_ambiguous_meridiem"]:
        candidate["needs_confirmation"] = True
        candidate["confidence"] = "medium"
        candidate["reason"] = "Có giờ bắt đầu nhưng chưa rõ sáng hay chiều."
    elif duration_minutes:
        candidate["confidence"] = "high"
        candidate["reason"] = "Có giờ bắt đầu và thời lượng rõ ràng."
    else:
        candidate["confidence"] = "medium"
        candidate["reason"] = "Có giờ bắt đầu nhưng chưa có thời lượng."

    return candidate


def _build_range_hint_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    parsed_time = item.get("parsed_time")

    if not isinstance(parsed_time, dict):
        return None

    if parsed_time.get("time_type") != "range_hint":
        return None

    return {
        "candidate_type": "time_range_hint",
        "range_hint": parsed_time.get("range_hint"),
        "approx_start_hour": parsed_time.get("approx_start_hour"),
        "approx_end_hour": parsed_time.get("approx_end_hour"),
        "needs_confirmation": True,
        "confidence": "low",
        "reason": "Thời gian mới là khoảng chung, chưa có giờ cụ thể.",
    }


def _build_deadline_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    parsed_deadline = item.get("parsed_deadline")

    if not isinstance(parsed_deadline, dict):
        return None

    deadline_type = parsed_deadline.get("deadline_type")

    if deadline_type == "before_time":
        return {
            "candidate_type": "deadline_before_time",
            "deadline": {
                "hour": parsed_deadline.get("hour"),
                "minute": parsed_deadline.get("minute", 0),
                "text": parsed_deadline.get("text"),
            },
            "needs_confirmation": bool(parsed_deadline.get("is_ambiguous_meridiem")),
            "confidence": "medium",
            "reason": "Có deadline theo giờ nhưng chưa có giờ bắt đầu.",
        }

    if deadline_type == "relative_day":
        return {
            "candidate_type": "deadline_relative_day",
            "deadline": {
                "day_hint": parsed_deadline.get("day_hint"),
                "text": parsed_deadline.get("text"),
            },
            "needs_confirmation": True,
            "confidence": "low",
            "reason": "Có deadline theo ngày nhưng chưa có giờ cụ thể.",
        }

    return None


def _build_schedule_candidate(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Ưu tiên:
    1. Giờ bắt đầu cụ thể
    2. Khoảng thời gian như sáng/chiều/tối
    3. Deadline
    """
    exact_candidate = _build_exact_time_candidate(item)
    if exact_candidate:
        return exact_candidate

    range_candidate = _build_range_hint_candidate(item)
    if range_candidate:
        return range_candidate

    deadline_candidate = _build_deadline_candidate(item)
    if deadline_candidate:
        return deadline_candidate

    return None


def _add_scheduler_summary(item: Dict[str, Any]) -> None:
    candidate = item.get("schedule_candidate")

    summary = {
        "has_schedule_candidate": candidate is not None,
        "candidate_type": None,
        "can_create_calendar_event": False,
        "needs_confirmation": False,
    }

    if isinstance(candidate, dict):
        summary["candidate_type"] = candidate.get("candidate_type")
        summary["needs_confirmation"] = bool(candidate.get("needs_confirmation"))

        if candidate.get("candidate_type") in ["exact_start_time", "exact_start_end_time"]:
            summary["can_create_calendar_event"] = True

    item["scheduler_summary"] = summary


def scheduler_reason(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      output sau temporal_reason

    Output:
      thêm schedule_candidate vào từng item.
    """
    result = copy.deepcopy(data)
    issues: List[str] = []

    items = result.get("items", [])

    if not isinstance(items, list):
        result["items"] = []
        return {
            "data": result,
            "issues": ["scheduler_items_not_list_reset"],
        }

    processed_items: List[Dict[str, Any]] = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"scheduler_invalid_item_skipped:{idx}")
            continue

        candidate = _build_schedule_candidate(item)

        item["schedule_candidate"] = candidate

        if candidate is None:
            issues.append(f"no_schedule_candidate:item_{idx}:{item.get('title')}")
            item["scheduler_notes"] = ["Chưa đủ dữ liệu để tạo lịch."]
        else:
            item["scheduler_notes"] = [candidate.get("reason")]

        _add_scheduler_summary(item)
        processed_items.append(item)

    result["items"] = processed_items

    return {
        "data": result,
        "issues": issues,
    }