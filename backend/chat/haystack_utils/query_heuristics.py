# chat/haystack_utils/query_heuristics.py

import re
from typing import Optional


_REF_STRONG_HINTS = (
    "integrations api",
    "integration api",
    "/reference/",
    "reference/",
    "api reference",
    "module ",
    "class ",
    "def ",
    "__init__",
    "signature",
    "parameters",
    "init variables",
    "returns",
    "env",
    "variables",
    "haystack_integrations.",
)


_REF_SOFT_HINTS = (
    "validator",
    "router",
    "builder",
    "generator",
    "store",
    "invoker",
)


_ARCH_HINTS = (
    "jak zbudowac",
    "jak zbudować",
    "jak powinien wygladac",
    "jak powinien wyglądać",
    "jak wyglada",
    "jak wygląda",
    "jak dziala",
    "jak działa",
    "architektura",
    "schemat",
    "struktura",
    "flow",
    "workflow",
    "przeplyw",
    "przepływ",
    "polaczyc",
    "połączyć",
    "connect",
    "add_component",
)


_CONCEPTUAL_PREFIXES = (
    "co to",
    "czym jest",
    "wyjaśnij",
    "wyjasnij",
    "explain",
    "opisz",
    "what is",
    "what are",
    "what does",
    "what is the role of",
    "what is the difference between",
    "how does",
    "how do",
    "why does",
    "why do",
    "difference between",
    "role of",
    "jak działa",
    "jak dziala",
    "jaka jest różnica",
    "jaka jest roznica",
)


_COMPARISON_HINTS = (
    " vs ",
    " versus ",
    "difference between",
    "what is the difference between",
    "compare",
    "comparison",
    "porównaj",
    "porownaj",
    "jaka jest różnica",
    "jaka jest roznica",
    "czym się różni",
    "czym sie rozni",
    "różnica między",
    "roznica miedzy",
    "różni się od",
    "rozni sie od",
)


_GUIDE_HINTS = (
    "jak zbudować",
    "jak zbudowac",
    "jak zrobić",
    "jak zrobic",
    "jak użyć",
    "jak uzyc",
    "jak używa się",
    "jak uzywa sie",
    "how to",
    "how can i",
    "step by step",
    "krok po kroku",
    "jak połączyć",
    "jak polaczyc",
    "jak skonfigurować",
    "jak skonfigurowac",
    "jak wdrożyć",
    "jak wdrozyc",
    "jak uruchomić",
    "jak uruchomic",
    "how do i build",
    "how do i use",
    "how do i connect",
    "how do i configure",
)


_INTEGRATION_HINTS = (
    "integration",
    "integracja",
    "pgvector",
    "weaviate",
    "qdrant",
    "pinecone",
    "ollama",
    "openrouter",
    "openai",
    "anthropic",
    "mistral",
    "vertex",
    "bedrock",
    "faiss",
    "elasticsearch",
    "opensearch",
    "mongodb atlas",
    "chroma",
    "azure ai search",
    "cohere",
    "watsonx",
    "llama cpp",
    "llama-cpp",
)


_ARCHITECTURE_WORKFLOW_HINTS = (
    "architektura",
    "architecture",
    "flow",
    "workflow",
    "przepływ",
    "przeplyw",
    "jak działa",
    "jak dziala",
    "jak to działa",
    "jak to dziala",
    "jak wygląda",
    "jak wyglada",
    "how does",
    "how do",
    "end-to-end",
    "high level",
    "overview",
    "rola w systemie",
    "miejsce w systemie",
)


_TROUBLESHOOTING_HINTS = (
    "dlaczego",
    "czemu",
    "why",
    "problem",
    "issue",
    "error",
    "błąd",
    "blad",
    "exception",
    "traceback",
    "nie działa",
    "nie dziala",
    "doesn't work",
    "does not work",
    "not working",
    "jak naprawić",
    "jak naprawic",
    "jak poprawić",
    "jak poprawic",
    "jak debugować",
    "jak debugowac",
    "debug",
    "debugging",
    "słabe wyniki",
    "slabe wyniki",
    "low quality",
    "retrieval quality",
    "czemu nie znajduje",
    "czemu nie działa",
    "czemu nie dziala",
)


_COMPONENT_API_HINTS = (
    "parametr",
    "parametry",
    "parameters",
    "signature",
    "returns",
    "return value",
    "fields",
    "field",
    "pola",
    "pole",
    "methods",
    "method",
    "metody",
    "metoda",
    "arguments",
    "argument",
    "__init__",
    "class ",
    "def ",
    "api",
    "schema",
    "input",
    "output",
    "properties",
    "attributes",
    "atrybuty",
    "jakie ma pola",
    "jakie ma parametry",
    "jakie metody",
)


_COMPARISON_STOPWORDS = {
    "co", "to", "jest", "czym", "jaka", "jaki", "jakie", "jak", "rola",
    "rolą", "rolą", "roli", "wyjasnij", "wyjaśnij", "opisz", "porownaj",
    "porównaj", "miedzy", "między", "roznica", "różnica", "sie", "się",
    "od", "a", "i", "oraz", "vs", "versus", "difference", "between",
    "compare", "comparison", "class", "api", "haystack", "w",
}


def normalize_query(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"^\s*\d+[\.\)\-:]*\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def looks_like_conceptual_question(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)

    if q.startswith(_CONCEPTUAL_PREFIXES):
        return True

    wrapper_patterns = (
        r"^(w dokumentacji|na podstawie dokumentacji|na podstawie docs|na podstawie docsa|powiedz mi|pokaż mi|pokaz mi)\s+",
        r"^(czy możesz|czy mozesz|możesz|mozesz)\s+",
    )

    q2 = q
    for pattern in wrapper_patterns:
        q2 = re.sub(pattern, "", q2).strip()

    return q2.startswith(_CONCEPTUAL_PREFIXES)


def looks_like_comparison_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)
    return _contains_any(q, _COMPARISON_HINTS)


def looks_like_guide_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)
    return _contains_any(q, _GUIDE_HINTS)


def _extract_component_candidates(text: str) -> list[str]:
    q = normalize_query(text)

    tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_-]+\b", q)
    candidates = [
        tok for tok in tokens
        if tok not in _COMPARISON_STOPWORDS and len(tok) >= 4
    ]

    seen = set()
    ordered: list[str] = []
    for token in candidates:
        if token not in seen:
            ordered.append(token)
            seen.add(token)

    return ordered


def extract_component_name(text: str) -> Optional[str]:
    """
    Try to extract a likely component / class name from a query,
    even if the query has already been normalized to lowercase.

    Examples:
    - "Jakie parametry ma ChatMessage" -> "chatmessage"
    - "jakie parametry ma chatmessage" -> "chatmessage"
    - "fields of PgvectorDocumentStore" -> "pgvectordocumentstore"
    """
    if not text:
        return None

    q = normalize_query(text)

    stopwords = {
        "jakie", "jaki", "jak", "ma", "maja", "mają", "parametry", "parametr",
        "pola", "pole", "metody", "metoda", "fields", "field", "methods",
        "method", "arguments", "argument", "properties", "attributes",
        "co", "to", "jest", "czym", "dla", "of", "the", "class", "api",
        "haystack", "w",
    }

    tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_-]+\b", q)
    candidates = [tok for tok in tokens if tok not in stopwords and len(tok) >= 4]

    if not candidates:
        return None

    candidates.sort(key=len, reverse=True)
    return candidates[0]


def extract_comparison_component_names(text: str) -> list[str]:
    """
    Extract up to 2 likely component names from a comparison query.

    Supports patterns like:
    - "ConditionalRouter vs MetadataRouter"
    - "difference between ConditionalRouter and MetadataRouter"
    - "jaka jest różnica między ConditionalRouter a MetadataRouter"
    - "porównaj ToolInvoker i ConditionalRouter"
    """
    if not text:
        return []

    q = normalize_query(text)

    patterns = [
        r"(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+vs\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+versus\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"difference between\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+and\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"what is the difference between\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+and\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"jaka jest różnica między\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+a\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"jaka jest roznica miedzy\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+a\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"różnica między\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+a\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"roznica miedzy\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+a\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"porównaj\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+i\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"porownaj\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+i\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
        r"compare\s+(?P<a>[a-zA-Z_][a-zA-Z0-9_-]{3,})\s+and\s+(?P<b>[a-zA-Z_][a-zA-Z0-9_-]{3,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            a = match.group("a").strip().lower()
            b = match.group("b").strip().lower()

            components = []
            for candidate in (a, b):
                if candidate not in _COMPARISON_STOPWORDS and candidate != "haystack":
                    components.append(candidate)

            if len(components) == 2 and components[0] != components[1]:
                return components

    candidates = _extract_component_candidates(q)

    if len(candidates) >= 2:
        return candidates[:2]

    return candidates[:1]


def looks_like_integration_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)

    provider_hints = (
        "pgvector",
        "weaviate",
        "qdrant",
        "pinecone",
        "ollama",
        "openrouter",
        "openai",
        "anthropic",
        "mistral",
        "vertex",
        "bedrock",
        "faiss",
        "elasticsearch",
        "opensearch",
        "mongodb atlas",
        "chroma",
        "azure ai search",
        "cohere",
        "watsonx",
        "llama cpp",
        "llama-cpp",
    )

    if _contains_any(q, provider_hints):
        return True

    if "integration" in q or "integracja" in q:
        return True

    return False


def looks_like_architecture_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)
    return _contains_any(q, _ARCHITECTURE_WORKFLOW_HINTS)


def looks_like_troubleshooting_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)
    return _contains_any(q, _TROUBLESHOOTING_HINTS)


def looks_like_component_api_query(text: str) -> bool:
    if not text:
        return False

    q = normalize_query(text)
    return _contains_any(q, _COMPONENT_API_HINTS)


def classify_doc_query_type(text: str) -> Optional[str]:
    """
    Return a higher-level documentation query type.

    Priority matters:
    - troubleshooting should win over most other classes
    - comparison should win over conceptual wording
    - explicit integration keywords should win over generic how-to wording
    - guide/how-to should win over generic architecture wording
    - component_api should route more narrowly than generic conceptual
    """
    if not text:
        return None

    q = normalize_query(text)

    if looks_like_troubleshooting_query(q):
        return "troubleshooting"

    if looks_like_comparison_query(q):
        return "comparison"

    if looks_like_integration_query(q):
        return "integration"

    if looks_like_guide_query(q):
        return "guide_how_to"

    if looks_like_component_api_query(q):
        return "component_api"

    if looks_like_architecture_query(q):
        return "architecture_workflow"

    if looks_like_conceptual_question(q):
        return "conceptual"

    return None


def looks_like_reference_query(text: str) -> bool:
    if not text:
        return False

    qn = normalize_query(text)
    doc_query_type = classify_doc_query_type(qn)

    if doc_query_type in {
        "comparison",
        "guide_how_to",
        "integration",
        "architecture_workflow",
        "troubleshooting",
        "conceptual",
    }:
        return False

    if doc_query_type == "component_api":
        return True

    if any(h in qn for h in _REF_STRONG_HINTS):
        return True

    if " > " in qn:
        left, _, _right = qn.partition(" > ")
        if any(k in left for k in ("api", "integrations", "reference")):
            return True

    if any(h in qn for h in _ARCH_HINTS):
        return False

    if any(h in qn for h in _REF_SOFT_HINTS):
        return True

    return False