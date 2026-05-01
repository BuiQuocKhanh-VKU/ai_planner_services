from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from app.pipelines.infer_pipeline import run_infer_pipeline


class InferRequest(BaseModel):
    text: str
    base_date: str | None = None


class InferResponse(BaseModel):
    input_text: str
    raw_output: str

    normalized_output: Dict[str, Any]
    normalizer_issues: List[Any]

    semantic_output: Dict[str, Any]
    semantic_issues: List[Any]

    temporal_output: Dict[str, Any]
    temporal_issues: List[Any]

    client_response: Dict[str, Any]
    final_reply: Optional[str]
    items: List[Any]
    conflicts: List[Any]
    needs_user_confirmation: bool
    can_sync_calendar: bool
    
    planner_items_payload: List[Any]

app = FastAPI(
    title="AI Planner Service",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    result = run_infer_pipeline(
        text=req.text,
        base_date=req.base_date,
    )
    return InferResponse(**result)