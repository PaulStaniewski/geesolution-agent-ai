from contextvars import ContextVar
from typing import Optional
from .types import RetrieverResult

_retriever_calls_cv: ContextVar[int] = ContextVar("retriever_calls", default=0)
_last_retriever_result_cv: ContextVar[Optional[RetrieverResult]] = ContextVar(
    "last_retriever_result", default=None
)

def reset_retriever_guard() -> None:
    _retriever_calls_cv.set(0)
    _last_retriever_result_cv.set(None)

def get_retriever_calls() -> int:
    return _retriever_calls_cv.get()

def inc_retriever_calls() -> None:
    _retriever_calls_cv.set(get_retriever_calls() + 1)

def get_last_retriever_result() -> Optional[RetrieverResult]:
    return _last_retriever_result_cv.get()

def set_last_retriever_result(result: RetrieverResult) -> None:
    _last_retriever_result_cv.set(result)