from app.core.model_loader import load_model
from app.core.config import MAX_INPUT_LENGTH
from app.processors.json_normalizer import normalize_model_output
from app.processors.semantic_fixer import semantic_fix_v2
from app.processors.temporal_reasoner import temporal_reason
from app.processors.scheduler_reasoner import scheduler_reason
from app.processors.conflict_reasoner import conflict_reason
from app.processors.reply_finalizer import apply_reply_finalizer
from app.processors.response_builder import build_client_response
from app.processors.duration_reasoner import duration_reason
from app.processors.planner_mapper import build_planner_items_payload


def run_infer_pipeline(text: str, base_date: str | None = None) -> dict:
    tokenizer, model = load_model()

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_LENGTH
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        min_new_tokens=10,
        num_beams=1,
        do_sample=False,
        early_stopping=False
    )

    raw_output = tokenizer.decode(outputs[0], skip_special_tokens=True)

    normalized = normalize_model_output(raw_output)

    semantic_input = {
        **normalized["data"],
        "_original_input_text": text
    }

    semantic_fixed = semantic_fix_v2(semantic_input)
    temporal_fixed = temporal_reason(semantic_fixed["data"])
    duration_fixed = duration_reason(temporal_fixed["data"])
    scheduled = scheduler_reason(duration_fixed["data"])
    conflicted = conflict_reason(scheduled["data"])
    final_data = apply_reply_finalizer(conflicted["data"])

    combined_temporal_issues = (
        temporal_fixed["issues"]
        + duration_fixed["issues"]
        + scheduled["issues"]
        + conflicted["issues"]
    )

    client_response = build_client_response(
        final_data=final_data,
        normalizer_issues=normalized["issues"],
        semantic_issues=semantic_fixed["issues"],
        temporal_issues=combined_temporal_issues,
    )

    planner_items_payload = build_planner_items_payload(
    final_data=final_data,
    base_date=base_date,
    )

    return {
        "input_text": text,
        "raw_output": raw_output,

        "normalized_output": normalized["data"],
        "normalizer_issues": normalized["issues"],

        "semantic_output": semantic_fixed["data"],
        "semantic_issues": semantic_fixed["issues"],

        "temporal_output": final_data,
        "temporal_issues": combined_temporal_issues,

        "client_response": client_response,
        "final_reply": client_response["final_reply"],
        "items": client_response["items"],
        "conflicts": client_response["conflicts"],
        "needs_user_confirmation": client_response["needs_user_confirmation"],
        "can_sync_calendar": client_response["can_sync_calendar"],

        "planner_items_payload": planner_items_payload,
}