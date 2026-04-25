# chat/haystack_utils/planner.py
import re
from typing import List

from haystack.dataclasses import ChatMessage

from .schemas import ExecutionPlan

from .query_heuristics import (
    normalize_query,
    looks_like_conceptual_question,
    classify_doc_query_type,
)


def looks_like_filename_token(value: str) -> bool:
    """
    Heuristic check for whether a token looks like a stored document/file name.
    """
    if not value:
        return False

    token = value.strip().strip("\"'“”")
    if len(token) > 180:
        return False

    if re.search(r"\.(md|txt|pdf|docx)$", token, re.IGNORECASE):
        return True

    if (" " not in token) and ("/" in token or "\\" in token):
        return True

    return False


def extract_filename_from_question(question: str) -> str:
    """
    Extract a file token from general user questions like:
    - "o czym jest dokument2.txt?"
    - "co jest w dokument1.pdf"
    - "stresc plik raport.docx"
    """
    if not question:
        return ""

    match = re.search(
        r'(?P<tok>[^\s"\'“”]+?\.(?:md|txt|pdf|docx))',
        question,
        flags=re.IGNORECASE,
    )
    token = (match.group("tok") if match else "").strip()
    token = token.strip().strip(",.?!;:)")

    return token if looks_like_filename_token(token) else ""


def extract_filename_from_quiz_request(question: str) -> str:
    """
    Extract a file token from prompts like:
    - "zrob quiz na podstawie samplers-api.md"
    - "zrob quiz na podstawie: samplers-api.md"
    - "na podstawie 'samplers-api.md'"
    """
    if not question:
        return ""

    match = re.search(
        r"na podstawie\s*:?\s*(?:z\s+)?(?:pliku\s+)?[\"'“”]?(?P<tok>[^\s\"'“”]+)[\"'“”]?",
        question,
        flags=re.IGNORECASE,
    )
    token = (match.group("tok") if match else "").strip()
    token = token.strip().strip(",.?!;:)")

    return token if looks_like_filename_token(token) else ""


def detect_quiz_intent(question: str) -> bool:
    """
    Detect whether the user is asking for a quiz/test.
    """
    if not question:
        return False

    return bool(re.search(r"\b(quiz|quizz|test)\b", question, flags=re.IGNORECASE))


def detect_quiz_answers(question: str) -> bool:
    """
    Detect whether the message looks like quiz answers, e.g.:
    "1.a 2.b 3.c"
    """
    if not question:
        return False

    return bool(re.search(r"\b1\s*\.?\s*[a-d]\b", question, flags=re.IGNORECASE))


def rewrite_retrieval_query(question: str) -> str:
    """
    Light cleanup of user phrasing before retrieval.
    Keeps the query human-readable, but removes obvious wrapper phrases.
    """
    q = normalize_query(question)

    cleanup_phrases = [
        "na podstawie dokumentacji",
        "na podstawie docs",
        "na podstawie docsa",
        "na podstawie pliku",
        "na podstawie",
        "powiedz mi",
        "pokaz mi",
        "pokaż mi",
        "wytlumacz",
        "wytłumacz",
        "opisz",
        "prosze",
        "proszę",
    ]

    for phrase in cleanup_phrases:
        q = q.replace(phrase, " ")

    q = re.sub(r"\s+", " ", q).strip()

    return q


def enrich_integration_query(query: str) -> str:
    """
    Enrich integration-oriented queries with concrete integration symbols
    so retrieval can better match Haystack documentation filenames/titles.
    """
    q = normalize_query(query)

    if "ollama" in q:
        return (
            f"{q} "
            "ollama integration integrations-ollama "
            "ollamagenerator ollamachatgenerator "
            "ollamadocumentembedder ollamatextembedder"
        )

    if "weaviate" in q:
        return (
            f"{q} "
            "weaviate integration integrations-weaviate "
            "weaviatedocumentstore weaviatebm25retriever "
            "weaviateembeddingretriever weaviatehybridretriever"
        )

    if "qdrant" in q:
        return (
            f"{q} "
            "qdrant integration integrations-qdrant "
            "qdrant-document-store qdrantembeddingretriever "
            "qdrantsparseembeddingretriever qdranthybridretriever"
        )

    if "pgvector" in q:
        return (
            f"{q} "
            "pgvector integration integrations-pgvector "
            "pgvectordocumentstore pgvectorembeddingretriever "
            "pgvectorkeywordretriever"
        )

    return q


def choose_retrieval_mode(question: str, doc_query_type: str | None = None) -> str:
    """
    Decide which corpus mode should be preferred for retrieval.
    """
    q = normalize_query(question)
    doc_type = doc_query_type or classify_doc_query_type(q)

    if doc_type == "component_api":
        return "haystack_reference"

    if doc_type in {
        "comparison",
        "guide_how_to",
        "integration",
        "architecture_workflow",
        "troubleshooting",
        "conceptual",
    }:
        return "haystack_all"

    reference_signals = [
        "api",
        "reference",
        "class",
        "def",
        "__init__",
        "parametr",
        "parametry",
        "parameters",
        "signature",
        "returns",
        "module",
        "init variables",
        "haystack_integrations.",
        "/reference/",
        "reference/",
    ]

    if any(signal in q for signal in reference_signals):
        return "haystack_reference"

    return "haystack_all"


def choose_retrieval_top_k(question: str, doc_query_type: str | None = None) -> int:
    q = normalize_query(question)
    doc_type = doc_query_type or classify_doc_query_type(q)

    if doc_type == "component_api":
        return 4

    if doc_type == "conceptual":
        return 5

    if doc_type == "guide_how_to":
        return 7

    if doc_type == "integration":
        return 7

    if doc_type == "comparison":
        return 8

    if doc_type == "architecture_workflow":
        return 8

    if doc_type == "troubleshooting":
        return 8

    broad_signals = [
        "jak powinien wygladac",
        "jak powinien wyglądać",
        "jak zbudowac",
        "jak zbudować",
        "architektura",
        "schemat",
        "struktura",
        "pipeline",
        "flow",
        "architecture",
        "how does",
        "how do",
        "difference between",
        "role of",
    ]

    if any(signal in q for signal in broad_signals):
        return 6

    return 4


def should_retrieve(question: str) -> bool:
    """
    Decide whether document retrieval should be triggered.
    """
    lowered = normalize_query(question)
    if not lowered:
        return False

    if re.fullmatch(
        r"(cześć|czesc|hej|helo|hello|siema|yo|dzień dobry|dzien dobry|dobry wieczór|dobry wieczor|elo|witam)[!?. ]*",
        lowered,
    ):
        return False

    doc_query_type = classify_doc_query_type(lowered)
    if doc_query_type is not None:
        return True

    tech_signals = [
        "haystack",
        "pipeline",
        "agent",
        "retriever",
        "retrieval",
        "generator",
        "tool",
        "toolset",
        "pgvector",
        "documentstore",
        "bm25",
        "embedding",
        "prompt",
        "chat",
        "openai",
        "anthropic",
        "component",
        "components",
        "integrations",
        "api",
        "reference",
        "documentation",
        "dokumentacja",
        ".md",
        ".pdf",
        ".docx",
        ".txt",
    ]

    if any(signal in lowered for signal in tech_signals):
        return True

    if len(lowered) < 18:
        return False

    return False


def choose_file_target_mode(file_token: str) -> str:
    """
    Decide which retrieval scope should be used for direct filename queries.
    Current project rule:
    - markdown files are treated as Haystack docs by default
    - txt/pdf/docx files are treated as user uploads
    """
    if not file_token:
        return "haystack_all"

    lowered = file_token.lower()

    if lowered.endswith(".md"):
        return "haystack_all"

    if lowered.endswith((".txt", ".pdf", ".docx")):
        return "user"

    return "haystack_all"


def looks_like_exhaustive_file_query(question: str) -> bool:
    """
    Detect prompts that likely require broad coverage of a single file,
    e.g. "wymień wszystkie", "pełna lista", "without skipping any".
    """
    if not question:
        return False

    q = normalize_query(question)

    exhaustive_signals = [
        "wszystkie",
        "wymien wszystkie",
        "wymień wszystkie",
        "pelna lista",
        "pełna lista",
        "bez pomijania",
        "lista wszystkich",
        "podaj wszystkie",
        "wypisz wszystkie",
        "list all",
        "all ",
        "every ",
        "full list",
        "without skipping",
    ]

    return any(signal in q for signal in exhaustive_signals)


def build_execution_plan(
    question: str,
    history: List[ChatMessage] | None = None,
) -> ExecutionPlan:
    question_full = (question or "").strip()

    is_quiz_intent = detect_quiz_intent(question_full)
    is_quiz_answer = detect_quiz_answers(question_full)
    is_quiz = is_quiz_intent or is_quiz_answer

    quiz_file_token = ""
    use_fast_path_quiz = False

    target_file_token = extract_filename_from_question(question_full)

    if is_quiz and not is_quiz_answer:
        quiz_file_token = extract_filename_from_quiz_request(question_full)
        use_fast_path_quiz = bool(quiz_file_token)

    print("[PLANNER FILE DETECT]", {
        "question": question_full,
        "target_file_token": target_file_token,
        "quiz_file_token": quiz_file_token,
    })

    needs_retrieval = should_retrieve(question_full) and (not is_quiz_answer)

    doc_query_type = classify_doc_query_type(question_full) if needs_retrieval else None

    intent = "chat"
    route = "agent_plain"

    if is_quiz_answer:
        intent = "quiz_answer"
        route = "quiz_evaluation"
    elif use_fast_path_quiz:
        intent = "quiz_fast_path"
        route = "fast_quiz"
    elif is_quiz:
        intent = "quiz"
        route = "agent_plain"
    elif needs_retrieval:
        intent = "doc_qa"
        route = "agent_with_retrieval"

    response_mode = "assistant_text"
    if use_fast_path_quiz:
        response_mode = "html_quiz"

    run_agent = route not in ("fast_quiz", "quiz_evaluation")

    retrieval_query = rewrite_retrieval_query(question_full) if needs_retrieval else None
    if needs_retrieval and doc_query_type == "integration" and retrieval_query:
        retrieval_query = enrich_integration_query(retrieval_query)

    if needs_retrieval:
        if target_file_token and not is_quiz:
            retrieval_mode = choose_file_target_mode(target_file_token)
        else:
            retrieval_mode = choose_retrieval_mode(question_full, doc_query_type)
    else:
        retrieval_mode = None

    retrieval_top_k = (
        choose_retrieval_top_k(question_full, doc_query_type)
        if needs_retrieval
        else None
    )

    full_file_mode = bool(
        needs_retrieval
        and target_file_token
        and not is_quiz
        and looks_like_exhaustive_file_query(question_full)
    )

    if full_file_mode:
        retrieval_top_k = max(retrieval_top_k or 4, 20)

    inject_context = route == "agent_with_retrieval"

    print("[PLANNER RETURN]", {
        "intent": intent,
        "route": route,
        "retrieval_mode": retrieval_mode,
        "target_file_token": target_file_token or None,
        "retrieval_top_k": retrieval_top_k,
        "full_file_mode": full_file_mode,
    })

    return ExecutionPlan(
        intent=intent,
        route=route,
        is_quiz=is_quiz,
        is_quiz_answer=is_quiz_answer,
        use_fast_path_quiz=use_fast_path_quiz,
        quiz_file_token=quiz_file_token or None,
        target_file_token=target_file_token or None,
        needs_retrieval=needs_retrieval,
        retrieval_query=retrieval_query,
        retrieval_mode=retrieval_mode,
        retrieval_top_k=retrieval_top_k,
        inject_context=inject_context,
        run_agent=run_agent,
        response_mode=response_mode,
        doc_query_type=doc_query_type,
        full_file_mode=full_file_mode,
    )