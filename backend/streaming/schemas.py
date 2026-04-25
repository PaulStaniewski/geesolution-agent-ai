# streaming/schemas.py
from typing import List, Optional, Any
from pydantic import BaseModel

class RunMetrics(BaseModel):
    model: str
    mode: str
    latency_ms: int
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    routed: bool = False

class RetrievalHit(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str

class Trace(BaseModel):
    hits: List[RetrievalHit] = []
    tool_calls: Optional[List[Any]] = None

class AnswerPayload(BaseModel):
    text: Optional[str] = None              # dla TL;DR / QA / Cloud
    json_payload: Optional[Any] = None      # dla extract-json (Local)
    metrics: RunMetrics
    trace: Trace

class CompareResponse(BaseModel):
    cloud: AnswerPayload
    local: AnswerPayload

class QuestionIn(BaseModel):
    query: str
    user_id: int
    conversation_id: Optional[int] = None
    model: Optional[str] = None          # <— dla single analyze
    file_name: Optional[str] = None
    

class CompareIn(BaseModel):
    query: str
    user_id: int
    conversation_id: Optional[int] = None
    model_a: str                          
    model_b: str
    file_name: Optional[str] = None  