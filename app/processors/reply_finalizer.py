from typing import Any, Dict, List, Optional


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_sort_minutes(item: Dict[str, Any]) -> int:
    parsed_time = item.get("parsed_time") or {}

    if parsed_time.get("time_type") == "clock_time":
        hour = parsed_time.get("hour")
        minute = parsed_time.get("minute", 0)

        if isinstance(hour, int):
            if not isinstance(minute, int):
                minute = 0

            return hour * 60 + minute

    return 999999


def _format_time_phrase(time_text: Optional[str]) -> Optional[str]:
    if not time_text:
        return None

    t = time_text.strip().lower()

    relative_day_map = {
        "mai": "vào ngày mai",
        "ngày mai": "vào ngày mai",
        "hôm nay": "hôm nay",
        "tối nay": "tối nay",
        "sáng mai": "vào sáng mai",
        "chiều mai": "vào chiều mai",
        "tối mai": "vào tối mai",
    }

    if t in relative_day_map:
        return relative_day_map[t]

    return f"lúc {time_text}"


def _build_item_phrase(item: Dict[str, Any]) -> Optional[str]:
    title = _safe_str(item.get("title"))
    time_text = _safe_str(item.get("time_text"))
    person = _safe_str(item.get("person"))
    location = _safe_str(item.get("location"))

    if not title:
        return None

    parts = [title]

    if person:
        parts.append(f"với {person}")

    if location:
        parts.append(f"ở {location}")


    time_phrase = _format_time_phrase(time_text)
    if time_phrase:
        parts.append(time_phrase)

    return " ".join(parts)


def _join_phrases_vi(phrases: List[str]) -> str:
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} và {phrases[1]}"
    return f"{', '.join(phrases[:-1])}, và {phrases[-1]}"


def _replace_item_count_vi(text: str, n: int) -> str:
    import re

    patterns = [
        r"(\bghi nhận\s+)\d+(\s+(mục|việc))",
        r"(\btách được\s+)\d+(\s+(mục|việc))",
        r"(\bhiểu được\s+)\d+(\s+(mục|việc))",
        r"(\bđã hiểu\s+)\d+(\s+(mục|việc))",
    ]

    updated = text
    for p in patterns:
        updated_new = re.sub(p, rf"\g<1>{n}\g<2>", updated, flags=re.IGNORECASE)
        if updated_new != updated:
            return updated_new

    return text


def _fallback_reply(items: List[Dict[str, Any]]) -> str:
    sorted_items = sorted(items, key=_extract_sort_minutes)
    phrases = [_build_item_phrase(item) for item in sorted_items[:3]]
    phrases = [p for p in phrases if p]

    n = len(items)
    if n == 0:
        return "Tôi chưa trích xuất được mục nào rõ ràng từ note này."
    if n == 1:
        return f"Tôi đã ghi nhận 1 mục: {phrases[0]}."
    if n <= 3:
        return f"Tôi đã ghi nhận {n} mục: {_join_phrases_vi(phrases)}."
    extra = n - 3
    return f"Tôi đã ghi nhận {n} mục: {_join_phrases_vi(phrases)} và {extra} mục khác."


def _build_conflict_warning(data: Dict[str, Any]) -> Optional[str]:
    conflict_summary = data.get("conflict_summary") or {}
    conflicts = data.get("conflicts") or []

    if not isinstance(conflict_summary, dict):
        return None

    if not conflict_summary.get("has_conflicts"):
        return None

    if not isinstance(conflicts, list) or not conflicts:
        count = conflict_summary.get("conflict_count", 1)
        return f"Tuy nhiên, có {count} điểm cần kiểm tra vì lịch có khả năng bị trùng."

    first_conflict = conflicts[0]

    if not isinstance(first_conflict, dict):
        return "Tuy nhiên, có lịch cần kiểm tra vì có khả năng bị trùng."

    item_indexes = first_conflict.get("item_indexes") or []
    items = data.get("items") or []

    picked_items = []

    if isinstance(items, list):
        for idx in item_indexes:
            if isinstance(idx, int) and 0 <= idx < len(items):
                item = items[idx]
                if isinstance(item, dict):
                    picked_items.append(item)

    # Ưu tiên lấy item thật để warning đúng thứ tự giờ tăng dần
    if len(picked_items) >= 2:
        picked_items = sorted(picked_items, key=_extract_sort_minutes)

        item_a = picked_items[0]
        item_b = picked_items[1]

        title_a = _safe_str(item_a.get("title")) or "mục thứ nhất"
        title_b = _safe_str(item_b.get("title")) or "mục thứ hai"
        time_a = _safe_str(item_a.get("time_text"))
        time_b = _safe_str(item_b.get("time_text"))

        if time_a and time_b:
            return (
                f"Tuy nhiên, bạn cần kiểm tra lại vì '{title_a}' lúc {time_a} "
                f"có thể bị trùng với '{title_b}' lúc {time_b}."
            )

        return (
            f"Tuy nhiên, bạn cần kiểm tra lại vì '{title_a}' "
            f"có thể bị trùng với '{title_b}'."
        )

    # Fallback nếu không lấy được item từ index
    titles = first_conflict.get("titles") or []
    time_texts = first_conflict.get("time_texts") or []

    title_a = titles[0] if len(titles) > 0 else "mục thứ nhất"
    title_b = titles[1] if len(titles) > 1 else "mục thứ hai"

    time_a = time_texts[0] if len(time_texts) > 0 else None
    time_b = time_texts[1] if len(time_texts) > 1 else None

    if time_a and time_b:
        return (
            f"Tuy nhiên, bạn cần kiểm tra lại vì '{title_a}' lúc {time_a} "
            f"có thể bị trùng với '{title_b}' lúc {time_b}."
        )

    return (
        f"Tuy nhiên, bạn cần kiểm tra lại vì '{title_a}' "
        f"có thể bị trùng với '{title_b}'."
    )


def _append_conflict_warning(reply: str, data: Dict[str, Any]) -> str:
    warning = _build_conflict_warning(data)

    if not warning:
        return reply

    reply = reply.rstrip()

    if not reply.endswith("."):
        reply += "."

    return f"{reply} {warning}"

def build_reply_draft_final(data: Dict[str, Any]) -> str:
    items = data.get("items", [])
    if not isinstance(items, list):
        items = []

    sorted_items = sorted(items, key=_extract_sort_minutes)

    model_reply = _safe_str(data.get("reply_draft"))
    n = len(sorted_items)

    phrases = [_build_item_phrase(item) for item in sorted_items[:3]]
    phrases = [p for p in phrases if p]
    summary = _join_phrases_vi(phrases)

    if not model_reply:
        return _fallback_reply(sorted_items)

    updated = _replace_item_count_vi(model_reply, n)

    if summary:
        updated = updated.rstrip(". ")
        updated = f"{updated}: {summary}."

    updated = _append_conflict_warning(updated, data)

    return updated


def apply_reply_finalizer(data: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(data)
    result["reply_draft_from_model"] = result.get("reply_draft")
    result["reply_draft_final"] = build_reply_draft_final(result)
    return result