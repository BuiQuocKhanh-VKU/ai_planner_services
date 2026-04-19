from typing import Any, Dict, List, Optional


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_sort_hour(item: Dict[str, Any]) -> int:
    parsed_time = item.get("parsed_time") or {}
    if parsed_time.get("time_type") == "clock_time":
        return int(parsed_time.get("hour", 999))
    return 999


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

    if time_text:
        parts.append(f"lúc {time_text}")

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
    sorted_items = sorted(items, key=_extract_sort_hour)
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


def build_reply_draft_final(data: Dict[str, Any]) -> str:
    items = data.get("items", [])
    if not isinstance(items, list):
        items = []

    sorted_items = sorted(items, key=_extract_sort_hour)

    model_reply = _safe_str(data.get("reply_draft"))
    n = len(sorted_items)

    phrases = [_build_item_phrase(item) for item in sorted_items[:3]]
    phrases = [p for p in phrases if p]
    summary = _join_phrases_vi(phrases)

    if not model_reply:
        return _fallback_reply(sorted_items)

    updated = _replace_item_count_vi(model_reply, n)

    if summary:
        if updated.endswith("."):
            updated = updated[:-1]
        updated = f"{updated}: {summary}."

    return updated


def apply_reply_finalizer(data: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(data)
    result["reply_draft_from_model"] = result.get("reply_draft")
    result["reply_draft_final"] = build_reply_draft_final(result)
    return result