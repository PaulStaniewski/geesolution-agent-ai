import re
from typing import List


def looks_like_enumeration_request(question: str) -> bool:
    """
    Detect requests that ask for a complete list / enumeration.
    """
    q = (question or "").strip().lower()
    if not q:
        return False

    signals = [
        "wymień",
        "wymien",
        "wypisz",
        "podaj wszystkie",
        "lista wszystkich",
        "pełna lista",
        "pelna lista",
        "list all",
        "show all",
        "without skipping",
        "bez pomijania",
    ]
    return any(signal in q for signal in signals)


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []

    for item in items:
        clean = (item or "").strip()
        if not clean:
            continue
        if clean in seen:
            continue
        seen.add(clean)
        out.append(clean)

    return out


def extract_generator_names_from_text(text: str) -> List[str]:
    """
    Deterministically extract generator-like component names from full file content.

    Targets names such as:
    - OpenAIGenerator
    - OpenAIChatGenerator
    - DALLEImageGenerator
    - HuggingFaceLocalGenerator
    - FallbackChatGenerator
    - LLM
    """
    if not text:
        return []

    patterns = [
        r"\b([A-Z][A-Za-z0-9]*(?:ChatGenerator|ImageGenerator|Generator))\b",
        r"\b(LLM)\b",
    ]

    matches: List[str] = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text))

    return _dedupe_keep_order(matches)


def format_enumeration_answer(
    *,
    file_name: str,
    label_plural: str,
    items: List[str],
) -> str:
    if not items:
        return f"Nie udało się jednoznacznie wyłuskać pełnej listy z pliku `{file_name}`."

    lines = [
        f"W pliku `{file_name}` znalazłem następujące {label_plural}:",
        "",
    ]

    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. {item}")

    lines.append("")
    lines.append(f"Łącznie: **{len(items)}**")

    return "\n".join(lines)


def try_extract_full_file_answer(
    *,
    question: str,
    file_name: str,
    context_text: str,
) -> str:
    """
    Try to produce a deterministic answer for exhaustive single-file queries.

    Returns:
    - non-empty string -> deterministic answer ready to return
    - empty string     -> no deterministic extraction available, fallback to agent
    """
    q = (question or "").lower()
    fn = (file_name or "").lower()

    if not context_text.strip():
        return ""

    if not looks_like_enumeration_request(question):
        return ""

    # Targeted path for generator listings
    if "generator" in q or "generatory" in q or "generators" in fn:
        names = extract_generator_names_from_text(context_text)
        if names:
            return format_enumeration_answer(
                file_name=file_name,
                label_plural="generatory",
                items=names,
            )

    return ""