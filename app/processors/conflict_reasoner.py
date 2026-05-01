import copy
from typing import Any, Dict, List, Optional


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, int):
        return value
    return None


def _time_obj_to_minutes(time_obj: Any) -> Optional[int]:
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

    return day_offset * 24 * 60 + hour * 60 + minute


def _get_candidate_interval(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    candidate = item.get("schedule_candidate")

    if not isinstance(candidate, dict):
        return None

    start = _time_obj_to_minutes(candidate.get("start"))
    end = _time_obj_to_minutes(candidate.get("end"))

    if start is None:
        return None

    return {
        "start": start,
        "end": end,
        "candidate_type": candidate.get("candidate_type"),
        "needs_confirmation": bool(candidate.get("needs_confirmation")),
    }


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def _build_conflict(
    item_a: Dict[str, Any],
    item_b: Dict[str, Any],
    index_a: int,
    index_b: int,
    conflict_type: str,
    reason: str,
) -> Dict[str, Any]:
    return {
        "conflict_type": conflict_type,
        "item_indexes": [index_a, index_b],
        "titles": [
            item_a.get("title"),
            item_b.get("title"),
        ],
        "time_texts": [
            item_a.get("time_text"),
            item_b.get("time_text"),
        ],
        "severity": "medium",
        "needs_confirmation": True,
        "reason": reason,
    }


def _mark_item_conflict(item: Dict[str, Any], conflict_type: str) -> None:
    if "conflict_flags" not in item or not isinstance(item["conflict_flags"], list):
        item["conflict_flags"] = []

    if conflict_type not in item["conflict_flags"]:
        item["conflict_flags"].append(conflict_type)

    item["has_conflict"] = True


def conflict_reason(data: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(data)
    issues: List[str] = []

    items = result.get("items", [])

    if not isinstance(items, list):
        result["items"] = []
        result["conflicts"] = []
        result["conflict_summary"] = {
            "has_conflicts": False,
            "conflict_count": 0,
        }

        return {
            "data": result,
            "issues": ["conflict_items_not_list_reset"],
        }

    intervals = []

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(f"conflict_invalid_item_skipped:{idx}")
            continue

        item["has_conflict"] = False
        item["conflict_flags"] = []

        interval = _get_candidate_interval(item)

        if interval:
            intervals.append({
                "index": idx,
                "item": item,
                "interval": interval,
            })

    conflicts: List[Dict[str, Any]] = []

    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            a = intervals[i]
            b = intervals[j]

            a_interval = a["interval"]
            b_interval = b["interval"]

            a_start = a_interval["start"]
            a_end = a_interval["end"]

            b_start = b_interval["start"]
            b_end = b_interval["end"]

            item_a = a["item"]
            item_b = b["item"]

            # Cả hai có start/end đầy đủ
            if a_end is not None and b_end is not None:
                if _overlap(a_start, a_end, b_start, b_end):
                    conflict = _build_conflict(
                        item_a,
                        item_b,
                        a["index"],
                        b["index"],
                        "hard_time_overlap",
                        "Hai mục có khoảng thời gian bị chồng lấn.",
                    )
                    conflicts.append(conflict)
                    _mark_item_conflict(item_a, "hard_time_overlap")
                    _mark_item_conflict(item_b, "hard_time_overlap")

            # A có duration, B chỉ có start
            elif a_end is not None and b_end is None:
                if a_start <= b_start < a_end:
                    conflict = _build_conflict(
                        item_a,
                        item_b,
                        a["index"],
                        b["index"],
                        "soft_time_overlap",
                        "Một mục có thời lượng bao phủ giờ bắt đầu của mục còn lại.",
                    )
                    conflicts.append(conflict)
                    _mark_item_conflict(item_a, "soft_time_overlap")
                    _mark_item_conflict(item_b, "soft_time_overlap")

            # B có duration, A chỉ có start
            elif a_end is None and b_end is not None:
                if b_start <= a_start < b_end:
                    conflict = _build_conflict(
                        item_a,
                        item_b,
                        a["index"],
                        b["index"],
                        "soft_time_overlap",
                        "Một mục có thời lượng bao phủ giờ bắt đầu của mục còn lại.",
                    )
                    conflicts.append(conflict)
                    _mark_item_conflict(item_a, "soft_time_overlap")
                    _mark_item_conflict(item_b, "soft_time_overlap")

            # Cả hai chỉ có start giống nhau
            else:
                if a_start == b_start:
                    conflict = _build_conflict(
                        item_a,
                        item_b,
                        a["index"],
                        b["index"],
                        "same_start_time",
                        "Hai mục có cùng giờ bắt đầu.",
                    )
                    conflicts.append(conflict)
                    _mark_item_conflict(item_a, "same_start_time")
                    _mark_item_conflict(item_b, "same_start_time")

    result["items"] = items
    result["conflicts"] = conflicts
    result["conflict_summary"] = {
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
    }

    return {
        "data": result,
        "issues": issues,
    }