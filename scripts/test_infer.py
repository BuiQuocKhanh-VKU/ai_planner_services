import os
import sys
import json

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PROJECT_ROOT)

from app.pipelines.infer_pipeline import run_infer_pipeline

if __name__ == "__main__":
    text = "Tôi sẽ làm bài tập với Nam ở thư viện lúc 2 giờ và 3 giờ đi làm bài tập ở trường VKU"
    result = run_infer_pipeline(text)

    print("INPUT:")
    print(result["input_text"])

    print("\nRAW OUTPUT:")
    print(result["raw_output"])

    print("\nNORMALIZED OUTPUT:")
    print(json.dumps(result["normalized_output"], ensure_ascii=False, indent=2))

    print("\nSEMANTIC OUTPUT:")
    print(json.dumps(result["semantic_output"], ensure_ascii=False, indent=2))

    print("\nTEMPORAL OUTPUT:")
    print(json.dumps(result["temporal_output"], ensure_ascii=False, indent=2))

    print("\nTEMPORAL ISSUES:")
    print(result["temporal_issues"])

    print("\nREPLY DRAFT FINAL:")
    print(result["temporal_output"].get("reply_draft_final"))