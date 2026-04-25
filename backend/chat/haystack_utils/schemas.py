from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionPlan:
    """
    Describes how the runtime should handle the current user request.

    This is intentionally small and explicit:
    - classify request intent,
    - decide whether retrieval is needed,
    - decide whether a quiz fast-path should be used,
    - define whether the Haystack agent should run.
    """

    intent: str
    route: str

    is_quiz: bool
    is_quiz_answer: bool

    use_fast_path_quiz: bool
    quiz_file_token: Optional[str]

    # General file targeting for non-quiz document queries
    target_file_token: Optional[str] = None

    needs_retrieval: bool = False
    retrieval_query: Optional[str] = None
    retrieval_mode: Optional[str] = None
    retrieval_top_k: Optional[int] = None

    # NEW: force full-file retrieval for exhaustive single-file queries
    full_file_mode: bool = False

    inject_context: bool = False

    doc_query_type: Optional[str] = None

    run_agent: bool = True
    response_mode: str = "assistant_text"


@dataclass
class ExecutionResult:
    text: str
    html: bool = False
    used_fast_path: bool = False
    used_retrieval: bool = False