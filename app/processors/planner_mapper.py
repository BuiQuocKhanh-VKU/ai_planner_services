import copy
from datetime import datetime, date, time, timedelta, timezone
from typing import Any, Dict, List, Optional


VN_TZ = timezone(timedelta(hours=7))


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    return None


def _get_base_date(base_date: Optional[str] = None) -> date:
    """
    base_date format: YYYY-MM-DD.
    Nếu backend không truyền thì mặc định lấy ngày hiện tại theo VN timezone.
    """
    if base_date:
        try:
            return datetime.strptime(base_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    return datetime.now(VN_TZ).date()


def _time_obj_to_datetime(time_obj: Any, base: date) -> Optional[datetime]:
    if not isinstance(time_obj, dict):
        return None

    hour = _safe_int(time_obj.get("hour"))
    minute = time_obj.get("minute", 0)
    day_offset = time_obj.get("day_offset", 0)

    if hour is None:
        return None

    if not isinstance(minute, int):
        minute = 0

    if not isinstance(day_offset, int):
        day_offset = 0

    if hour < 0 or hour > 23:
        return None

    if minute < 0 or minute > 59:
        minute = 0

    target_date = base + timedelta(days=day_offset)

    return datetime.combine(
        target_date,
        time(hour=hour, minute=minute),
        tzinfo=VN_TZ
    )


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat()


def _get_duration_minutes(item: Dict[str, Any]) -> Optional[int]:
    duration_resolution = item.get("duration_resolution")
    if isinstance(duration_resolution, dict):
        minutes = duration_resolution.get("duration_minutes")
        if isinstance(minutes, int) and minutes > 0:
            return minutes

    parsed_duration = item.get("parsed_duration")
    if isinstance(parsed_duration, dict):
        minutes = parsed_duration.get("minutes")
        if isinstance(minutes, int) and minutes > 0:
            return minutes

    candidate = item.get("schedule_candidate")
    if isinstance(candidate, dict):
        minutes = candidate.get("duration_minutes")
        if isinstance(minutes, int) and minutes > 0:
            return minutes

    return None


def _map_one_item_to_planner_payload(
    item: Dict[str, Any],
    index: int,
    base: date,
) -> Dict[str, Any]:
    candidate = item.get("schedule_candidate")
    if not isinstance(candidate, dict):
        candidate = {}

    start_at = _time_obj_to_datetime(candidate.get("start"), base)
    end_at = _time_obj_to_datetime(candidate.get("end"), base)

    duration_minutes = _get_duration_minutes(item)

    duration_resolution = item.get("duration_resolution")
    is_duration_default = False
    if isinstance(duration_resolution, dict):
        is_duration_default = bool(duration_resolution.get("is_default"))

    needs_duration_confirmation = False
    if isinstance(duration_resolution, dict):
        needs_duration_confirmation = bool(
            duration_resolution.get("needs_duration_confirmation")
        )
        

    return {
        # Backend sẽ tự thêm id, user_id, chat_session_id, source_message_id nếu cần
        "client_temp_id": f"ai_item_{index}",

        "item_type": item.get("item_type") or "task",
        "title": item.get("title"),
        "description": None,

        "source_text": item.get("source_text"),
        "raw_ai_data": copy.deepcopy(item),

        "constraints_text": item.get("constraint_text"),
        "location_text": item.get("location"),

        "start_at": _to_iso(start_at),
        "end_at": _to_iso(end_at),
        "due_at": None,

        "duration_minutes": duration_minutes,
        "priority": item.get("priority") or "medium",

        "status": "draft",
        "is_all_day": False,
        "is_flexible": bool(
            isinstance(duration_resolution, dict)
            and duration_resolution.get("is_flexible")
        ),

        "is_duplicate_suspected": False,
        "duplicate_note": None,

        "google_event_id": None,
        "sync_status": "not_synced",
        "last_synced_at": None,

        "created_by_ai": True,

        # Field phụ cho app/backend quyết định UI
        "can_sync_calendar": _can_sync_calendar_item(item),
        "needs_confirmation": bool(item.get("needs_confirmation")),
        "has_conflict": bool(item.get("has_conflict")),
        "conflict_flags": item.get("conflict_flags", []),
        "needs_duration_confirmation": needs_duration_confirmation,

        "ai_meta": {
            "index": index,
            "time_text": item.get("time_text"),
            "duration_text": item.get("duration_text"),
            "deadline_text": item.get("deadline_text"),
            "parsed_time": item.get("parsed_time"),
            "parsed_duration": item.get("parsed_duration"),
            "parsed_deadline": item.get("parsed_deadline"),
            "duration_resolution": duration_resolution,
            "is_duration_default": is_duration_default,
            "schedule_candidate": item.get("schedule_candidate"),
            "semantic_flags": item.get("semantic_flags", []),
            "temporal_flags": item.get("temporal_flags", []),
        },
    }

def _can_sync_calendar_item(item: Dict[str, Any]) -> bool:
    candidate = item.get("schedule_candidate")

    if not isinstance(candidate, dict):
        return False

    if candidate.get("candidate_type") != "exact_start_end_time":
        return False

    if candidate.get("needs_confirmation"):
        return False

    if item.get("needs_confirmation"):
        return False

    if item.get("needs_time_confirmation"):
        return False

    if item.get("has_conflict"):
        return False

    start = candidate.get("start")
    end = candidate.get("end")

    if not isinstance(start, dict) or not isinstance(end, dict):
        return False

    return True

def build_planner_items_payload(
    final_data: Dict[str, Any],
    base_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Chuyển output cuối của AI pipeline sang payload planner_items.
    base_date dùng để gắn ngày cho các giờ như 20:00, 21:00.
    """
    data = copy.deepcopy(final_data)
    base = _get_base_date(base_date)

    items = data.get("items", [])
    if not isinstance(items, list):
        return []

    mapped_items: List[Dict[str, Any]] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        mapped_items.append(
            _map_one_item_to_planner_payload(
                item=item,
                index=index,
                base=base,
            )
        )

    return mapped_items