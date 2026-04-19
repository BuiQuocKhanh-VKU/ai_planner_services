from app.core.model_loader import load_model
from app.core.config import MAX_INPUT_LENGTH
from app.processors.json_normalizer import normalize_model_output
from app.processors.semantic_fixer import semantic_fix_v2
from app.processors.reply_finalizer import apply_reply_finalizer
from app.processors.temporal_reasoner import temporal_reason


def run_infer_pipeline(text: str) -> dict:
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
    temporal_fixed["data"] = apply_reply_finalizer(temporal_fixed["data"])


    return {
        "input_text": text,
        "raw_output": raw_output,
        "normalized_output": normalized["data"],
        "normalizer_issues": normalized["issues"],
        "semantic_output": semantic_fixed["data"],
        "semantic_issues": semantic_fixed["issues"],
        "temporal_output": temporal_fixed["data"],
        "temporal_issues": temporal_fixed["issues"],
    }