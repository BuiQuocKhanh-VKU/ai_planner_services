import os
import sys
import json

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.append(PROJECT_ROOT)

from app.pipelines.infer_pipeline import run_infer_pipeline

if __name__ == "__main__":
    text = "Sáng nay tại quán cà phê ABC tôi sẽ uống cà phê từ 7h đến 11h và làm bài tập nhóm tại quán đó từ 8h đến 10h "
    result = run_infer_pipeline(text)

    print("INPUT:")
    print(result["input_text"])

    # print("\nRAW OUTPUT:")
    # print(result["raw_output"])

    # print("\nNORMALIZED OUTPUT:")
    # print(json.dumps(result["normalized_output"], ensure_ascii=False, indent=2))

    # print("\nSEMANTIC OUTPUT:")
    # print(json.dumps(result["semantic_output"], ensure_ascii=False, indent=2))

    # print("\nTEMPORAL OUTPUT:")
    # print(json.dumps(result["temporal_output"], ensure_ascii=False, indent=2))

    # print("\nTEMPORAL ISSUES:")
    # print(result["temporal_issues"])

    # print("\nREPLY DRAFT FINAL:")
    # print(result["temporal_output"].get("reply_draft_final"))

    print("\nCLIENT RESPONSE:")
    print(json.dumps(result.get("client_response"), ensure_ascii=False, indent=2))

    print("\nFINAL REPLY:")
    print(result.get("final_reply"))

    print("\nNEEDS USER CONFIRMATION:")
    print(result.get("needs_user_confirmation"))

    print("\nCAN SYNC CALENDAR:")
    print(result.get("can_sync_calendar"))

    print("\nCONFLICTS:")
    print(json.dumps(result.get("conflicts"), ensure_ascii=False, indent=2))