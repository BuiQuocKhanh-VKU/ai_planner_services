from transformers import T5Tokenizer, AutoModelForSeq2SeqLM
from app.core.config import MODEL_PATH

tokenizer = None
model = None

BASE_TOKENIZER_NAME = "google/mt5-small"


def load_model():
    global tokenizer, model

    if tokenizer is None or model is None:
        print("MODEL_PATH =", MODEL_PATH)

        tokenizer = T5Tokenizer.from_pretrained(
            BASE_TOKENIZER_NAME,
            legacy=True
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)

        print("Loaded model config:", model.config._name_or_path)

    return tokenizer, model