import copy
import re
from typing import Any, Dict, List, Optional


TIME_VAGUE_WORDS = {
    "sáng", "trưa", "chiều", "tối", "đêm",
    "hôm nay", "sáng nay", "trưa nay", "chiều nay", "tối nay",
    "ngày mai", "mai", "sáng mai", "mai sáng",
    "chiều mai", "mai chiều", "tối mai", "mai tối",
    "tuần này"
}

EVENT_HINTS = {
    "họp", "gặp", "meeting", "call", "phỏng vấn", "trao đổi", "hẹn","lên lịch làm việc",
    "làm việc với", "họp team", "lên kế hoạch", "họp nhóm", "họp với", "gặp gỡ", "gặp mặt", "gặp nhau", "gặp bạn", "gặp đồng nghiệp", "gặp sếp", "gặp khách hàng", "họp dự án"
}

TASK_HINTS = {
    "làm", "hoàn thành", "soạn", "viết", "nộp", "gửi", "đọc", "ôn", "học",
    "review", "chuẩn bị", "báo cáo", "bài tập", "slide", "tài liệu", "làm thêm"
}

HABIT_HINTS = {
    "gym", "tập gym", "chạy bộ", "đọc sách", "thiền", "uống thuốc", "ăn sáng", "đi ngủ"
}

# BỎ "đi" ra khỏi danh sách nhiễu
NOISE_PREFIX_WORDS = {
    "nhớ", "thì", "mà", "là", "phải", "sẽ", "cần", "giúp", "hãy", "định", "tôi sẽ"
}

BAD_TITLES_EXACT = {
    "việc", "công việc", "task", "event", "habit"
}


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    value = str(value).strip()
    return value or None


def _norm_space(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _remove_polite_tail(text: Optional[str]) -> Optional[str]:
    t = _norm_space(text)
    if not t:
        return None

    t = re.sub(r"\s+(nhé|nha|ạ|nhe|với)\s*$", "", t, flags=re.IGNORECASE)
    return _norm_space(t)


def _looks_like_duration_phrase(text: Optional[str]) -> bool:
    t = _remove_polite_tail(text)
    if not t:
        return False

    t = t.lower()

    patterns = [
        r"^(trong\s+)?\d{1,3}\s*(tiếng|giờ|phút)$",
        r"^\d{1,2}\s*giờ\s*rưỡi$",
    ]

    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)


def _clean_title_noise(text: Optional[str]) -> Optional[str]:
    t = _norm_space(text)
    if not t:
        return None

    # Bỏ modal/chủ ngữ đầu câu
    t = re.sub(r"^\s*tôi\s+sẽ\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*tôi\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*sẽ\s+", "", t, flags=re.IGNORECASE)

    # Bỏ cụm thời gian tương đối
    t = re.sub(
        r"\b(tối nay|sáng nay|chiều nay|hôm nay|ngày mai|mai|tối mai|sáng mai|chiều mai)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )

    # Bỏ giờ cụ thể: 20h, 20 giờ, 20:00
    t = re.sub(
        r"\b(lúc|vào|tầm|khoảng)?\s*\d{1,2}(?::\d{2})?\s*(h|giờ)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )

    # Bỏ duration: trong 1 tiếng, 1 tiếng, 30 phút, 1 giờ rưỡi
    t = re.sub(
        r"\btrong\s+\d{1,3}\s*(tiếng|giờ|phút)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b\d{1,3}\s*(tiếng|phút)\b",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(
        r"\b\d{1,2}\s*giờ\s*rưỡi\b",
        "",
        t,
        flags=re.IGNORECASE,
    )

    t = _remove_polite_tail(t)
    if not t:
        return None

    return _norm_space(t.strip(" ,.-:"))

def _lower(text: Optional[str]) -> str:
    return _norm_space(text).lower() if text else ""


def _ensure_meta(item: Dict[str, Any]) -> None:
    if "semantic_flags" not in item or not isinstance(item["semantic_flags"], list):
        item["semantic_flags"] = []
    if "fix_notes" not in item or not isinstance(item["fix_notes"], list):
        item["fix_notes"] = []
    if "needs_confirmation" not in item:
        item["needs_confirmation"] = False


def _flag(item: Dict[str, Any], name: str) -> None:
    _ensure_meta(item)
    if name not in item["semantic_flags"]:
        item["semantic_flags"].append(name)


def _note(item: Dict[str, Any], msg: str) -> None:
    _ensure_meta(item)
    item["fix_notes"].append(msg)


def _confirm(item: Dict[str, Any], msg: str) -> None:
    _ensure_meta(item)
    item["needs_confirmation"] = True
    item["fix_notes"].append(msg)


def _normalize_title_basic(title: Optional[str]) -> Optional[str]:
    title = _norm_space(title)
    if not title:
        return None

    t = re.sub(r"^[,\-:\s]+", "", title)
    words = t.split()

    # Chỉ bỏ prefix thật sự là nhiễu
    while words and words[0].lower() in NOISE_PREFIX_WORDS:
        words.pop(0)

    t = " ".join(words).strip(" ,.-:")
    return _norm_space(t)


def _tokenize(text: Optional[str]) -> List[str]:
    t = _lower(text)
    t = re.sub(r"[^\w\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]", " ", t)
    return [x for x in t.split() if x]


def _jaccard(a: Optional[str], b: Optional[str]) -> float:
    sa = set(_tokenize(a))
    sb = set(_tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _extract_all_clock_times(text: Optional[str]) -> List[str]:
    t = _lower(text)
    if not t:
        return []
    matches = re.findall(r"\b\d{1,2}(?::\d{2})?\s*(?:giờ|h)\b", t)
    return [_norm_space(m) for m in matches if _norm_space(m)]


def _extract_duration_phrases(text: Optional[str]) -> List[str]:
    t = _lower(text)
    if not t:
        return []
    matches = re.findall(r"\b\d{1,2}\s*(?:tiếng|phút|giờ rưỡi)\b", t)
    return [_norm_space(m) for m in matches if _norm_space(m)]


def _guess_item_type(title: Optional[str], current_type: Optional[str]) -> str:
    t = _lower(title)
    if not t:
        return current_type or "task"

    if any(h in t for h in HABIT_HINTS):
        return "habit"
    if any(h in t for h in EVENT_HINTS):
        return "event"
    if any(h in t for h in TASK_HINTS):
        return "task"
    return current_type or "task"



def _source_context(original_input_text: str) -> List[str]:
    text = _norm_space(original_input_text) or ""
    if not text:
        return []

    # Tách các connector lập lịch phổ biến.
    # Ví dụ:
    # "20 giờ và tập đàn..."
    # "21 giờ sau đó đi ngủ..."
    parts = re.split(
        r"\s+(?:và|rồi|sau đó|xong rồi|tiếp đó|tiếp theo|kế đó)\s+|,\s*",
        text,
        flags=re.IGNORECASE
    )

    parts = [_norm_space(p) for p in parts if _norm_space(p)]
    return parts



def _match_best_source_fragment(item: Dict[str, Any], original_input_text: str) -> Optional[str]:
    title = item.get("title")
    if not title or not original_input_text:
        return None

    fragments = _source_context(original_input_text)
    best_fragment = None
    best_score = 0.0

    for frag in fragments:
        score = _jaccard(title, frag)
        if score > best_score:
            best_score = score
            best_fragment = frag

    return best_fragment if best_score >= 0.15 else None


def _clean_title(item: Dict[str, Any]) -> None:
    before = item.get("title")
    after = _normalize_title_basic(before)

    if after and after != before:
        item["title"] = after
        _flag(item, "title_cleaned")
        _note(item, f"title cleaned: '{before}' -> '{after}'")

    if _lower(item.get("title")) in BAD_TITLES_EXACT:
        _flag(item, "bad_title")
        _confirm(item, f"title too generic: '{item.get('title')}'")


def _fix_item_type(item: Dict[str, Any]) -> None:
    current = item.get("item_type")
    guessed = _guess_item_type(item.get("title"), current)

    if "đi làm thêm" in _lower(item.get("title")) and current != "task":
        item["item_type"] = "task"
        _flag(item, "item_type_corrected")
        _note(item, f"item_type corrected: '{current}' -> 'task'")
        return

    if guessed != current:
        item["item_type"] = guessed
        _flag(item, "item_type_corrected")
        _note(item, f"item_type corrected: '{current}' -> '{guessed}'")


def _fix_time_duration_deadline_using_source(item: Dict[str, Any], original_input_text: str) -> None:
    frag = item.get("source_text") or ""
    if not frag and original_input_text:
        frag = _match_best_source_fragment(item, original_input_text) or ""
        if frag:
            item["source_text"] = frag

    frag_l = _lower(frag)
    time_text = _lower(item.get("time_text"))
    deadline_text = _lower(item.get("deadline_text"))

    source_clock_times = _extract_all_clock_times(frag_l)
    source_durations = _extract_duration_phrases(frag_l)

    # Nếu source_text đã được gán riêng cho item và có giờ cụ thể,
    # ưu tiên giờ trong source_text hơn giờ model đoán.
    # Ví dụ: source_text = "22h làm bài tập" thì time_text phải là "22h",
    # dù model lỡ trả time_text = "20h".
    if source_clock_times:
        best_time = source_clock_times[0]
        current_time = item.get("time_text")

        if current_time != best_time:
            old = item.get("time_text")
            item["time_text"] = best_time
            _flag(item, "time_forced_from_source_fragment")
            _note(item, f"time_text forced from '{old}' to '{best_time}' using assigned source_text")

    # "lúc 2 giờ" => start time
    if re.search(r"\b(lúc|vào|tầm|khoảng)\s+\d{1,2}(?::\d{2})?\s*(giờ|h)\b", frag_l):
        if source_clock_times:
            best_time = source_clock_times[0]
            if item.get("time_text") != best_time:
                old = item.get("time_text")
                item["time_text"] = best_time
                _flag(item, "time_refined_from_source")
                _note(item, f"time_text refined from '{old}' to '{best_time}' using source fragment")

            if deadline_text and re.search(r"\btrước\s+\d{1,2}\s*(giờ|h)\b", deadline_text):
                old = item.get("deadline_text")
                item["deadline_text"] = None
                _flag(item, "deadline_removed_as_false_start_time")
                _note(item, f"deadline_text removed because source indicates start time, not deadline: '{old}'")

    # "2 tiếng" => duration
    if source_durations:
        best_duration = source_durations[0]
        if item.get("duration_text") != best_duration:
            old = item.get("duration_text")
            item["duration_text"] = best_duration
            _flag(item, "duration_refined_from_source")
            _note(item, f"duration_text refined from '{old}' to '{best_duration}' using source fragment")

    # thời gian quá mơ hồ nhưng source có giờ cụ thể
    if time_text in TIME_VAGUE_WORDS and source_clock_times:
        old = item.get("time_text")
        new_time = source_clock_times[0]
        if old != new_time:
            item["time_text"] = new_time
            _flag(item, "vague_time_replaced")
            _note(item, f"time_text replaced from vague '{old}' to '{new_time}'")


def _is_explicit_spurious(item: Dict[str, Any]) -> bool:
    title = _lower(item.get("title"))
    if not title:
        return True
    if title in BAD_TITLES_EXACT:
        return True

    # Chỉ remove mẫu rác rất cụ thể
    if title == "đi làm bài tập":
        return False

    return False

def _is_exact_clock_time_text(text: Optional[str]) -> bool:
    t = _lower(text)
    if not t:
        return False

    return bool(re.search(r"\b\d{1,2}(?::\d{2})?\s*(h|giờ)\b", t))


def _item_quality_score(item: Dict[str, Any]) -> int:
    score = 0

    if item.get("title"):
        score += 1

    if item.get("duration_text"):
        score += 2

    if item.get("source_text"):
        score += 2

    if item.get("deadline_text"):
        score += 1

    time_text = item.get("time_text")

    if _is_exact_clock_time_text(time_text):
        score += 8
    elif _lower(time_text) in TIME_VAGUE_WORDS:
        score += 2
    elif time_text:
        score += 1

    return score

def _score_item_info(item: Dict[str, Any]) -> int:
    return _item_quality_score(item)


def _score_item_fragment_match(item: Dict[str, Any], fragment: str) -> float:
    score = 0.0

    item_title = _lower(item.get("title"))
    frag_lower = _lower(fragment)

    # 1) title similarity
    score += _jaccard(item_title, frag_lower) * 3.0

    # 2) time match rất quan trọng
    item_time = _safe_str(item.get("time_text"))
    if item_time and item_time.lower() in frag_lower:
        score += 5.0

    # 3) duration match
    item_duration = _safe_str(item.get("duration_text"))
    if item_duration and item_duration.lower() in frag_lower:
        score += 2.0

    # 4) person/location đã có thì boost thêm
    item_person = _safe_str(item.get("person"))
    if item_person and item_person.lower() in frag_lower:
        score += 4.0

    item_location = _safe_str(item.get("location"))
    if item_location and item_location.lower() in frag_lower:
        score += 4.0

    return score


def _assign_source_fragments_one_to_one(items: List[Dict[str, Any]], original_input_text: str) -> None:
    """
    Gán source_text cho từng item theo kiểu 1 fragment chỉ dùng 1 lần.

    Bản cải tiến:
    - Ưu tiên match theo score.
    - Nếu item match kém nhưng còn fragment chưa dùng, gán fallback theo thứ tự.
    Nhờ vậy case:
    'Tối nay họp nhóm lúc 20h và 22h làm bài tập'
    vẫn cứu được item thứ 2 từ fragment '22h làm bài tập'.
    """
    fragments = _source_context(original_input_text)
    if not fragments:
        return

    used_fragment_indexes = set()

    for item_index, item in enumerate(items):
        best_idx = None
        best_score = -1.0

        for idx, frag in enumerate(fragments):
            if idx in used_fragment_indexes:
                continue

            score = _score_item_fragment_match(item, frag)
            if score > best_score:
                best_score = score
                best_idx = idx

        # Nếu match tốt thì dùng best fragment
        if best_idx is not None and best_score > 0:
            chosen = fragments[best_idx]
            item["source_text"] = chosen
            _flag(item, "source_text_assigned_1to1")
            _note(item, f"source_text assigned by 1-1 matching: '{chosen}'")
            used_fragment_indexes.add(best_idx)
            continue

        # Fallback: nếu model sinh title sai, vẫn gán fragment còn lại theo thứ tự
        fallback_idx = None

        if item_index < len(fragments) and item_index not in used_fragment_indexes:
            fallback_idx = item_index
        else:
            for idx in range(len(fragments)):
                if idx not in used_fragment_indexes:
                    fallback_idx = idx
                    break

        if fallback_idx is not None:
            chosen = fragments[fallback_idx]
            item["source_text"] = chosen
            _flag(item, "source_text_assigned_by_order_fallback")
            _note(item, f"source_text assigned by order fallback: '{chosen}'")
            used_fragment_indexes.add(fallback_idx)

def _refine_time_from_source_text(item: Dict[str, Any]) -> None:
    """
    Nếu source_text đã được gán chuẩn, dùng nó để sửa time_text rõ hơn.
    """
    frag = _safe_str(item.get("source_text"))
    if not frag:
        return

    frag_l = _lower(frag)
    source_clock_times = _extract_all_clock_times(frag_l)

    current_time = _safe_str(item.get("time_text"))

    # Nếu time hiện tại là vague và fragment có giờ cụ thể
    if current_time and _lower(current_time) in TIME_VAGUE_WORDS and source_clock_times:
        new_time = source_clock_times[0]
        if current_time != new_time:
            item["time_text"] = new_time
            _flag(item, "vague_time_replaced")
            _note(item, f"time_text replaced from vague '{current_time}' to '{new_time}'")


def _extract_title_from_source_text(text: Optional[str]) -> Optional[str]:
    """
    Cứu title từ source_text sau khi đã gán fragment.
    Ví dụ:
    - 'Tối nay 20h học tiếng Anh trong 1 tiếng nhé' -> 'học tiếng Anh'
    - '3 giờ đi làm bài tập ở trường VKU' -> 'đi làm bài tập'
    """
    t = _norm_space(text)
    if not t:
        return None

    # Bỏ chủ ngữ / modal đầu câu
    t = re.sub(r"^\s*tôi\s+sẽ\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*tôi\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^\s*sẽ\s+", "", t, flags=re.IGNORECASE)

    # Bỏ cụm thời gian ở đầu câu
    t = re.sub(
        r"^\s*(ngày\s+mai|mai|hôm\s+nay|tối\s+nay|sáng\s+mai|chiều\s+mai|tối\s+mai|sáng nay|chiều nay)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )

    # Bỏ giờ ở đầu câu: "20h học tiếng Anh..." -> "học tiếng Anh..."
    t = re.sub(
        r"^\s*\d{1,2}(?::\d{2})?\s*(giờ|h)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )

    # Cắt trước person/location/time/deadline/duration
    t = re.split(
        r"\s+(với|cùng|ở|tại|lúc|vào|tầm|khoảng|trước|sau|trong)\s+",
        t,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return _clean_title_noise(t)

def _remove_time_phrase_from_title(title: Optional[str]) -> Optional[str]:
    return _clean_title_noise(title)


def _fix_common_model_typos(item: Dict[str, Any]) -> None:
    title = _safe_str(item.get("title"))
    if not title:
        return

    typo_map = {
        "đi ngộ": "đi ngủ",
    }

    fixed = typo_map.get(title.lower())

    if fixed:
        old = item.get("title")
        item["title"] = fixed
        _flag(item, "title_typo_fixed")
        _note(item, f"title typo fixed: '{old}' -> '{fixed}'")


def _fix_false_duration_from_clock_time(item: Dict[str, Any]) -> None:
    """
    Model hay nhầm '20 giờ' thành duration_text '20 phút'.
    Nếu source_text không có duration thật thì xoá duration_text.
    """
    duration_text = _safe_str(item.get("duration_text"))
    source_text = _safe_str(item.get("source_text"))

    if not duration_text or not source_text:
        return

    source_l = source_text.lower()
    duration_l = duration_text.lower()

    duration_like_in_source = bool(
        re.search(r"\btrong\s+\d{1,3}\s*(phút|tiếng|giờ)\b", source_l)
        or re.search(r"\b\d{1,3}\s*(phút|tiếng)\b", source_l)
        or re.search(r"\b\d{1,2}\s*giờ\s*rưỡi\b", source_l)
    )

    if duration_like_in_source:
        return

    # Nếu duration là phút nhưng source chỉ có giờ đồng hồ
    if re.search(r"\b\d{1,3}\s*phút\b", duration_l):
        old = item.get("duration_text")
        item["duration_text"] = None
        _flag(item, "false_duration_removed")
        _note(item, f"duration_text removed because source_text has no real duration: '{old}'")


def _fix_title_using_source_text(item: Dict[str, Any]) -> None:
    """
    Nếu title model sai hoặc không khớp source_text,
    dùng source_text để cứu lại title tự nhiên hơn.
    Đồng thời xoá cụm giờ bị dính vào title:
    - 'học bài vào 20 giờ' -> 'học bài'
    """
    source_title = _extract_title_from_source_text(item.get("source_text"))
    current_title = _safe_str(item.get("title"))

    changed = False

    if source_title and not current_title:
        item["title"] = source_title
        _flag(item, "title_inferred_from_source")
        _note(item, f"title inferred from source_text: '{source_title}'")
        changed = True

    elif source_title and current_title:
        current_l = current_title.lower()
        source_l = source_title.lower()

        title_sim = _jaccard(current_l, source_l)

        # Case 1: source có "đi ..." nhưng title bị mất chữ "đi"
        if source_l.startswith("đi ") and not current_l.startswith("đi "):
            tail = source_l[3:].strip()

            if current_l == tail or tail in current_l or current_l in tail:
                old = item.get("title")
                item["title"] = source_title
                _flag(item, "title_refined_from_source")
                _note(item, f"title refined from '{old}' to '{source_title}' using source_text")
                changed = True

        # Case 2: title model hoàn toàn không liên quan source_text
        # Ví dụ: title = "thiền", source_title = "làm bài tập"
        if not changed and title_sim < 0.25:
            old = item.get("title")
            item["title"] = source_title
            _flag(item, "title_replaced_low_similarity_source")
            _note(item, f"title replaced from '{old}' to '{source_title}' because it mismatched source_text")
            changed = True

        # Case 3: source_title dài hơn và bao trùm current_title
        if not changed and current_l in source_l and len(source_l) > len(current_l) + 2:
            old = item.get("title")
            item["title"] = source_title
            _flag(item, "title_refined_from_source")
            _note(item, f"title refined from '{old}' to '{source_title}' using source_text")
            changed = True

    # Luôn chạy clean title cuối cùng để tránh:
    # "học bài vào 20 giờ lúc 20 giờ"
    cleaned_title = _remove_time_phrase_from_title(item.get("title"))

    if cleaned_title and cleaned_title != item.get("title"):
        old = item.get("title")
        item["title"] = cleaned_title
        _flag(item, "title_time_phrase_removed")
        _note(item, f"title time phrase removed: '{old}' -> '{cleaned_title}'")



def _same_or_empty(a: Optional[str], b: Optional[str]) -> bool:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    return a == b or not a or not b


def _should_consider_duplicate(item: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    item_title = _normalize_title_for_duplicate(item.get("title"))
    existing_title = _normalize_title_for_duplicate(existing.get("title"))

    title_sim = _jaccard(item_title, existing_title)
    if title_sim < 0.75:
        return False

    item_time = (item.get("time_text") or "").strip().lower()
    existing_time = (existing.get("time_text") or "").strip().lower()

    item_location = (item.get("location") or "").strip().lower()
    existing_location = (existing.get("location") or "").strip().lower()

    item_person = (item.get("person") or "").strip().lower()
    existing_person = (existing.get("person") or "").strip().lower()

    # Nếu cả hai có giờ cụ thể khác nhau thì không phải duplicate.
    # Nhưng nếu một bên là "tối nay/hôm nay/mai" còn một bên là "20h" thì vẫn coi là duplicate.
    if item_time and existing_time and item_time != existing_time:
        if item_time not in TIME_VAGUE_WORDS and existing_time not in TIME_VAGUE_WORDS:
            return False

    if item_location and existing_location and item_location != existing_location:
        return False

    if item_person and existing_person and item_person != existing_person:
        return False

    return True

def _normalize_title_for_duplicate(title: Optional[str]) -> str:
    t = _clean_title_noise(title)
    t = _lower(t)
    if not t:
        return ""

    t = re.sub(r"^\s*đi\s+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _remove_spurious_and_duplicates(items: List[Dict[str, Any]], issues: List[str]) -> List[Dict[str, Any]]:
    kept: List[Dict[str, Any]] = []

    for item in items:
        if _is_explicit_spurious(item):
            issues.append(f"spurious_item_removed:{item.get('title')}")
            continue

        duplicated = False
        for existing in kept:
            if _should_consider_duplicate(item, existing):
                if _score_item_info(item) <= _score_item_info(existing):
                    issues.append(f"duplicate_removed:{item.get('title')}~{existing.get('title')}")
                    duplicated = True
                    break
                else:
                    issues.append(f"duplicate_replaced:{existing.get('title')}~{item.get('title')}")
                    kept.remove(existing)
                    break

        if not duplicated:
            kept.append(item)

    return kept

def _inject_missing_source_text(items: List[Dict[str, Any]], original_input_text: str) -> None:
    for item in items:
        if not item.get("source_text"):
            frag = _match_best_source_fragment(item, original_input_text)
            if frag:
                item["source_text"] = frag
                _flag(item, "source_text_injected")
                _note(item, f"source_text injected from original input: '{frag}'")


def _mark_low_confidence(items: List[Dict[str, Any]]) -> None:
    for item in items:
        title = _lower(item.get("title"))
        time_text = _lower(item.get("time_text"))
        duration_text = _lower(item.get("duration_text"))
        deadline_text = _lower(item.get("deadline_text"))

        if not title:
            _confirm(item, "missing meaningful title")

        if time_text in TIME_VAGUE_WORDS and not duration_text and not deadline_text:
            _flag(item, "vague_time_text")
            _confirm(item, f"time_text is still vague: '{time_text}'")


def semantic_fix_v2(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    result = copy.deepcopy(normalized_data)
    issues: List[str] = []
    original_input_text = _safe_str(result.get("_original_input_text")) or ""

    raw_items = result.get("items", [])
    if not isinstance(raw_items, list):
        raw_items = []
        issues.append("items_reset_in_semantic_fix_v2")

    fixed_items: List[Dict[str, Any]] = []

    # Bước 1: clean item cơ bản trước
    for idx, raw_item in enumerate(raw_items):
        if not isinstance(raw_item, dict):
            issues.append(f"invalid_item_skipped:{idx}")
            continue

        item = copy.deepcopy(raw_item)
        _ensure_meta(item)

        _clean_title(item)
        _fix_item_type(item)

        fixed_items.append(item)

    # Bước 2: gán source fragment 1-1 trước
    if original_input_text:
        _assign_source_fragments_one_to_one(fixed_items, original_input_text)

    # Bước 3: sau khi đã có source_text đúng hơn, mới rescue time/person/location
    for item in fixed_items:
        if original_input_text:
            _fix_time_duration_deadline_using_source(item, original_input_text)
            _fix_false_duration_from_clock_time(item)
            _fix_deadline_duration_confusion(item)
            _fix_person_field(item, original_input_text)
            _fix_location_field(item, original_input_text)
            _refine_time_from_source_text(item)
            _fix_title_using_source_text(item)
            _fix_common_model_typos(item)
            _fix_item_type(item)

    # Bước 4: inject source nếu item nào vẫn chưa có
    if original_input_text:
        _inject_missing_source_text(fixed_items, original_input_text)

    # Bước 5: remove duplicate/spurious
    fixed_items = _remove_spurious_and_duplicates(fixed_items, issues)

    # Bước 6: mark low confidence
    _mark_low_confidence(fixed_items)

    result["items"] = fixed_items
    return {
        "data": result,
        "issues": issues,
    }


###############################  PERSON  #############################
def _extract_person_from_source_text(text: str) -> Optional[str]:
    if not text:
        return None

    text = _safe_str(text) or ""

    patterns = [
        r"\bvới\s+([A-ZÀ-Ỵ][a-zà-ỹ]*)(?=\s+(ở|lúc|vào|tại|cùng|với|và)\b|$)",
        r"\bgặp\s+([A-ZÀ-Ỵ][a-zà-ỹ]*)(?=\s+(ở|lúc|vào|tại|cùng|với|và)\b|$)",
        r"\bcùng\s+([A-ZÀ-Ỵ][a-zà-ỹ]*)(?=\s+(ở|lúc|vào|tại|cùng|với|và)\b|$)",
        r"\bvới anh\s+([A-ZÀ-Ỵ][a-zà-ỹ]*)(?=\s+(ở|lúc|vào|tại|cùng|với|và)\b|$)",
        r"\bvới chị\s+([A-ZÀ-Ỵ][a-zà-ỹ]*)(?=\s+(ở|lúc|vào|tại|cùng|với|và)\b|$)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1).strip()

    return None


def _looks_like_person_name(text: Optional[str]) -> bool:
    t = _safe_str(text)
    if not t:
        return False

    # 1-3 từ, viết hoa đầu từ, khá giống tên riêng tiếng Việt
    parts = t.split()
    if len(parts) > 4:
        return False

    return all(p[:1].isupper() for p in parts if p)


def _fix_person_field(item: Dict[str, Any], original_input_text: str) -> None:
    frag = item.get("source_text") or _match_best_source_fragment(item, original_input_text) or ""

    person = _extract_person_from_source_text(frag)

    if person and not item.get("person"):
        item["person"] = person
        _flag(item, "person_inferred_from_source")
        _note(item, f"person inferred from source_text: '{person}'")

    # cleanup case model parse sai: "trước Nghĩa"
    deadline_text = _safe_str(item.get("deadline_text"))
    if deadline_text and deadline_text.lower().startswith("trước "):
        tail = deadline_text[6:].strip()

        # nếu tail trùng person đã extract hoặc trông giống tên riêng thì bỏ deadline
        if (person and tail.lower() == person.lower()) or _looks_like_person_name(tail):
            old = item.get("deadline_text")
            item["deadline_text"] = None
            _flag(item, "deadline_removed_person_confusion")
            _note(item, f"deadline_text removed because it looked like a person name: '{old}'")




########################  LOCATION  #########################
def _extract_location_from_source_text(text: str) -> Optional[str]:
    if not text:
        return None

    text = _safe_str(text) or ""

    patterns = [
        r"\bở\s+([a-zA-ZÀ-Ỵà-ỵ0-9\s]+?)(?=\s+(lúc|vào|tầm|khoảng|trước|sau|với|cùng|và|trong)\b|$)",
        r"\btại\s+([a-zA-ZÀ-Ỵà-ỵ0-9\s]+?)(?=\s+(lúc|vào|tầm|khoảng|trước|sau|với|cùng|và|trong)\b|$)",
        r"\bở chỗ\s+([a-zA-ZÀ-Ỵà-ỵ0-9\s]+?)(?=\s+(lúc|vào|tầm|khoảng|trước|sau|với|cùng|và|trong)\b|$)",
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            location = m.group(1).strip(" ,.-:")
            location = _remove_polite_tail(location)

            if not location:
                continue

            # Không cho duration bị hiểu nhầm thành location
            if _looks_like_duration_phrase(location):
                continue

            return location

    return None

def _looks_like_location_text(text: Optional[str]) -> bool:
    t = _safe_str(text)
    if not t:
        return False

    keywords = [
        "thư viện", "trường", "công ty", "quán", "cafe", "cà phê",
        "phòng", "văn phòng", "nhà", "bệnh viện", "trung tâm", "sân",
        "shop", "siêu thị", "chợ"
    ]
    tl = t.lower()
    return any(k in tl for k in keywords)



def _fix_location_field(item: Dict[str, Any], original_input_text: str) -> None:
    frag = item.get("source_text") or _match_best_source_fragment(item, original_input_text) or ""

    location = _extract_location_from_source_text(frag)

    if location and not item.get("location"):
        item["location"] = location
        _flag(item, "location_inferred_from_source")
        _note(item, f"location inferred from source_text: '{location}'")

    # Nếu constraint_text thực ra là location thì kéo sang
    constraint_text = _safe_str(item.get("constraint_text"))
    if constraint_text and not item.get("location") and _looks_like_location_text(constraint_text):
        item["location"] = constraint_text
        item["constraint_text"] = None
        _flag(item, "location_moved_from_constraint")
        _note(item, f"location moved from constraint_text: '{constraint_text}'")



def _fix_deadline_duration_confusion(item: Dict[str, Any]) -> None:
    """
    Model hay nhầm 'trong 2 tiếng' thành deadline_text.
    Nếu deadline_text thực chất là duration thì xoá khỏi deadline_text.
    """
    deadline_text = _safe_str(item.get("deadline_text"))
    duration_text = _safe_str(item.get("duration_text"))

    if not deadline_text:
        return

    dl = deadline_text.lower()

    is_duration_like = bool(
        re.search(r"\btrong\s+\d{1,3}\s*(tiếng|giờ|phút)\b", dl)
        or re.search(r"\b\d{1,3}\s*(tiếng|giờ|phút)\b", dl)
    )

    if not is_duration_like:
        return

    if not duration_text:
        item["duration_text"] = deadline_text.replace("trong ", "").strip()
        _flag(item, "duration_moved_from_deadline")
        _note(item, f"duration_text moved from deadline_text: '{deadline_text}'")

    old = item.get("deadline_text")
    item["deadline_text"] = None
    _flag(item, "deadline_removed_duration_confusion")
    _note(item, f"deadline_text removed because it looked like duration: '{old}'")