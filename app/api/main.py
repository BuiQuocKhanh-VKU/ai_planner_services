from fastapi import FastAPI
from pydantic import BaseModel

from app.pipelines.infer_pipeline import run_infer_pipeline


class InferRequest(BaseModel):
    text: str


class InferResponse(BaseModel):
    input_text: str
    raw_output: str
    normalized_output: dict
    normalizer_issues: list
    semantic_output: dict
    semantic_issues: list
    temporal_output: dict
    temporal_issues: list


app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    result = run_infer_pipeline(req.text)
    return InferResponse(**result)