import copy
from typing import Any, Dict, List


def _has_any_item_confirmation(items: List[Dict[str, Any]]) -> bool:
    for item in items:
        if not isinstance(item, dict):
            continue

        if item.get("needs_confirmation"):
            return True

        if item.get("needs_time_confirmation"):
            return True

        schedule_candidate = item.get("schedule_candidate")
        if isinstance(schedule_candidate, dict) and schedule_candidate.get("needs_confirmation"):
            return True

        if item.get("has_conflict"):
            return True

    return False


def _can_sync_calendar_item(item: Dict[str, Any]) -> bool:
    """
    Một item chỉ nên sync calendar khi:
    - Có schedule_candidate
    - Candidate thuộc loại có giờ bắt đầu
    - Không cần xác nhận thêm
    - Không bị conflict
    """
    candidate = item.get("schedule_candidate")

    if not isinstance(candidate, dict):
        return False

    candidate_type = candidate.get("candidate_type")

    if candidate_type not in ["exact_start_time", "exact_start_end_time"]:
        return False

    if candidate.get("needs_confirmation"):
        return False

    if item.get("needs_time_confirmation"):
        return False

    if item.get("has_conflict"):
        return False

    return True


def _build_item_client_view(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    candidate = item.get("schedule_candidate")
    scheduler_summary = item.get("scheduler_summary") or {}

    return {
        "index": index,
        "item_type": item.get("item_type"),
        "title": item.get("title"),
        "time_text": item.get("time_text"),
        "duration_text": item.get("duration_text"),
        "deadline_text": item.get("deadline_text"),
        "priority": item.get("priority"),
        "person": item.get("person"),
        "location": item.get("location"),
        "source_text": item.get("source_text"),

        "parsed_time": item.get("parsed_time"),
        "parsed_duration": item.get("parsed_duration"),
        "parsed_deadline": item.get("parsed_deadline"),
        "duration_resolution": item.get("duration_resolution"),

        "schedule_candidate": candidate,
        "can_sync_calendar": _can_sync_calendar_item(item),

        "needs_confirmation": bool(
            item.get("needs_confirmation")
            or item.get("needs_time_confirmation")
            or scheduler_summary.get("needs_confirmation")
            or item.get("has_conflict")
        ),

        "has_conflict": bool(item.get("has_conflict")),
        "conflict_flags": item.get("conflict_flags", []),

        "semantic_flags": item.get("semantic_flags", []),
        "temporal_flags": item.get("temporal_flags", []),
        "fix_notes": item.get("fix_notes", []),
        "temporal_notes": item.get("temporal_notes", []),
        "scheduler_notes": item.get("scheduler_notes", []),
    }


def build_client_response(
    final_data: Dict[str, Any],
    normalizer_issues: List[str],
    semantic_issues: List[str],
    temporal_issues: List[str],
) -> Dict[str, Any]:
    """
    Gom output cuối thành format dễ dùng cho frontend/backend.
    Không thay thế temporal_output, chỉ tạo thêm client_response.
    """
    data = copy.deepcopy(final_data)

    items = data.get("items", [])
    if not isinstance(items, list):
        items = []

    client_items = []

    for idx, item in enumerate(items):
        if isinstance(item, dict):
            client_items.append(_build_item_client_view(item, idx))

    conflicts = data.get("conflicts", [])
    if not isinstance(conflicts, list):
        conflicts = []

    conflict_summary = data.get("conflict_summary") or {
        "has_conflicts": False,
        "conflict_count": 0,
    }

    needs_user_confirmation = bool(
        conflict_summary.get("has_conflicts")
        or _has_any_item_confirmation(items)
    )

    can_sync_calendar = bool(
        client_items
        and not needs_user_confirmation
        and all(item.get("can_sync_calendar") for item in client_items)
    )

    return {
        "final_reply": data.get("reply_draft_final"),
        "reply_draft_from_model": data.get("reply_draft_from_model"),

        "note_type": data.get("note_type"),
        "items": client_items,

        "conflicts": conflicts,
        "conflict_summary": conflict_summary,

        "needs_user_confirmation": needs_user_confirmation,
        "can_sync_calendar": can_sync_calendar,

        "issues": {
            "normalizer": normalizer_issues,
            "semantic": semantic_issues,
            "temporal": temporal_issues,
        },
    }