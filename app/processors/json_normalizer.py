import json
import re
from typing import Any, Dict, List, Optional, Tuple


ALLOWED_NOTE_TYPES = {
    "single_item",
    "single_item_plan",
    "multi_item_plan",
    "daily_plan",
    "weekly_plan",
    "general_note",
}

ALLOWED_ITEM_TYPES = {
    "task",
    "event",
    "habit",
    "reminder",
    "meeting",
    "study",
    "work",
    "personal",
    "other",
}

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return str(value).strip() or None


def _normalize_whitespace(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def _extract_json_block(text: str) -> str:
    text = text.strip()

    if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
        return text

    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        return obj_match.group(0)

    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        return arr_match.group(0)

    return text


def _try_parse_json(raw: Any) -> Tuple[Optional[Any], List[str]]:
    issues = []

    if isinstance(raw, (dict, list)):
        return raw, issues

    if not isinstance(raw, str):
        issues.append("raw_output_not_string_or_json")
        return None, issues

    text = raw.strip()
    if not text:
        issues.append("empty_raw_output")
        return None, issues

    candidates = []

    extracted = _extract_json_block(text)
    candidates.append(extracted)

    cleaned = _remove_trailing_commas(extracted)
    if cleaned != extracted:
        candidates.append(cleaned)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if candidate != text:
                issues.append("json_extracted_or_cleaned")
            return parsed, issues
        except json.JSONDecodeError:
            continue

    issues.append("json_parse_failed")
    return None, issues


def _normalize_note_type(value: Any, issues: List[str]) -> str:
    text = _safe_str(value)
    if not text:
        issues.append("missing_note_type_defaulted")
        return "general_note"

    text = text.lower().replace("-", "_").strip()

    alias_map = {
        "single": "single_item",
        "single_plan": "single_item_plan",
        "multi_item": "multi_item_plan",
        "multi-item": "multi_item_plan",
        "daily": "daily_plan",
        "weekly": "weekly_plan",
        "note": "general_note",
    }

    text = alias_map.get(text, text)

    if text not in ALLOWED_NOTE_TYPES:
        issues.append(f"invalid_note_type_defaulted:{text}")
        return "general_note"

    return text


def _normalize_item_type(value: Any, issues: List[str]) -> str:
    text = _safe_str(value)
    if not text:
        issues.append("missing_item_type_defaulted")
        return "task"

    text = text.lower().strip()

    alias_map = {
        "meeting": "event",
        "appointment": "event",
        "call": "event",
        "todo": "task",
    }

    text = alias_map.get(text, text)

    if text not in ALLOWED_ITEM_TYPES:
        issues.append(f"invalid_item_type_defaulted:{text}")
        return "task"

    return text


def _normalize_priority(value: Any, issues: List[str]) -> Optional[str]:
    text = _safe_str(value)
    if not text:
        return None

    text = text.lower().strip()

    alias_map = {
        "normal": "medium",
        "med": "medium",
        "important": "high",
        "very_high": "urgent",
    }

    text = alias_map.get(text, text)

    if text not in ALLOWED_PRIORITIES:
        issues.append(f"invalid_priority_dropped:{text}")
        return None

    return text


def _fallback_title_from_source(item: Dict[str, Any]) -> Optional[str]:
    source_text = _normalize_whitespace(_safe_str(item.get("source_text")))
    if not source_text:
        return None

    source_text = re.sub(r"^[,\-:\s]+", "", source_text)
    words = source_text.split()
    if not words:
        return None

    fallback = " ".join(words[:8]).strip(" ,.-:")
    return fallback or None


def _normalize_item(item: Any, idx: int, issues: List[str]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        issues.append(f"item_{idx}_not_object_replaced")
        item = {}

    title = _normalize_whitespace(_safe_str(item.get("title")))
    if not title:
        title = _fallback_title_from_source(item)
        if title:
            issues.append(f"item_{idx}_title_fallback_from_source_text")

    normalized = {
        "item_type": _normalize_item_type(item.get("item_type"), issues),
        "title": title,
        "time_text": _normalize_whitespace(_safe_str(item.get("time_text"))),
        "duration_text": _normalize_whitespace(_safe_str(item.get("duration_text"))),
        "deadline_text": _normalize_whitespace(_safe_str(item.get("deadline_text"))),
        "priority": _normalize_priority(item.get("priority"), issues),
        "person": _normalize_whitespace(_safe_str(item.get("person"))),
        "location": _normalize_whitespace(_safe_str(item.get("location"))),
        "constraint_text": _normalize_whitespace(_safe_str(item.get("constraint_text"))),
        "source_text": _normalize_whitespace(_safe_str(item.get("source_text"))),
    }

    if not normalized["title"]:
        issues.append(f"item_{idx}_missing_title")

    return normalized


def normalize_model_output(raw_output: Any) -> Dict[str, Any]:
    issues: List[str] = []

    parsed, parse_issues = _try_parse_json(raw_output)
    issues.extend(parse_issues)

    if parsed is None:
        return {
            "data": {
                "note_type": "general_note",
                "items": [],
                "global_constraints": [],
                "reply_draft": None,
            },
            "issues": issues,
        }

    if isinstance(parsed, list):
        parsed = {
            "note_type": "general_note",
            "items": parsed,
            "global_constraints": [],
            "reply_draft": None,
        }
        issues.append("top_level_list_wrapped_as_object")

    if not isinstance(parsed, dict):
        issues.append("top_level_not_object_reset")
        parsed = {}

    raw_items = parsed.get("items", [])
    if not isinstance(raw_items, list):
        issues.append("items_not_list_reset")
        raw_items = []

    raw_constraints = parsed.get("global_constraints", [])
    if raw_constraints is None:
        raw_constraints = []

    if isinstance(raw_constraints, str):
        raw_constraints = [raw_constraints]
        issues.append("global_constraints_string_wrapped")

    if not isinstance(raw_constraints, list):
        raw_constraints = []
        issues.append("global_constraints_invalid_reset")

    normalized_constraints = []
    for c in raw_constraints:
        c = _normalize_whitespace(_safe_str(c))
        if c:
            normalized_constraints.append(c)

    normalized_items = []
    for idx, item in enumerate(raw_items):
        normalized_items.append(_normalize_item(item, idx, issues))

    normalized = {
        "note_type": _normalize_note_type(parsed.get("note_type"), issues),
        "items": normalized_items,
        "global_constraints": normalized_constraints,
        "reply_draft": _normalize_whitespace(_safe_str(parsed.get("reply_draft"))),
    }

    return {
        "data": normalized,
        "issues": issues,
    }