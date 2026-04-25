from typing import List, Optional

from haystack.dataclasses import Document

from ...query_heuristics import extract_component_name


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _slug_variants(name: str) -> List[str]:
    """
    Build simple variants for matching component/file/page names.
    """
    raw = _normalize_text(name)
    if not raw:
        return []

    compact = raw.replace(" ", "").replace("-", "").replace("_", "")
    dashed = raw.replace(" ", "-").replace("_", "-")
    underscored = raw.replace(" ", "_").replace("-", "_")

    variants = {raw, compact, dashed, underscored}
    return [v for v in variants if v]


def _looks_like_integration_doc(file_name: str, title: str, nav_path: str, source_url: str) -> bool:
    blob = f"{file_name} {title} {nav_path} {source_url}"
    markers = [
        "integrations-",
        "/integrations/",
        "integration",
        "weaviate",
        "pgvector",
        "qdrant",
        "pinecone",
        "ollama",
        "openai",
        "anthropic",
        "mistral",
        "chroma",
        "elasticsearch",
        "opensearch",
        "mongodb",
        "bedrock",
        "cohere",
        "watsonx",
    ]
    return any(marker in blob for marker in markers)


def _looks_like_general_guide_doc(file_name: str, title: str, nav_path: str) -> bool:
    blob = f"{file_name} {title} {nav_path}"
    markers = [
        "creating-",
        "choosing-",
        "advanced-",
        "smart-",
        "debugging-",
        "pipeline",
        "pipelines",
        "agents",
        "components",
    ]
    return any(marker in blob for marker in markers)


def _apply_pattern_boosts(
    score: float,
    blob: str,
    file_name: str,
    title: str,
    source_url: str,
    patterns: List[str],
    strong_boost: float,
    weak_boost: float,
) -> float:
    for pattern in patterns:
        p = _normalize_text(pattern)
        if not p:
            continue

        if p in blob:
            if (
                p in file_name
                or p in title
                or f"/{p}" in source_url
                or f"-{p}" in file_name
                or f"{p}-" in file_name
            ):
                score += strong_boost
            else:
                score += weak_boost

    return score


def boost_by_filename_patterns(
    docs: List[Document],
    patterns: List[str],
    *,
    strong_boost: float = 0.35,
    weak_boost: float = 0.12,
    query: Optional[str] = None,
    component_name: Optional[str] = None,
    component_file_boost: float = 1.25,
    component_title_boost: float = 0.95,
    exact_file_boost: float = 2.40,
    exact_title_boost: float = 1.80,
    exact_url_boost: float = 1.80,
    integration_penalty: float = 0.45,
    guide_penalty: float = 0.20,
) -> List[Document]:
    """
    Re-score retrieved docs using technical-documentation-aware signals.

    Main goals:
    - strongly prefer the exact component page when it exists
    - still keep semantically related supporting docs
    - demote integration/tutorial pages for strict component queries
    """
    if not docs:
        return docs

    normalized_patterns = [_normalize_text(p) for p in patterns if p]
    rescored: List[Document] = []

    resolved_component_name = _normalize_text(component_name or "")
    if not resolved_component_name and query:
        resolved_component_name = _normalize_text(extract_component_name(query) or "")

    component_variants = _slug_variants(resolved_component_name)

    for d in docs:
        meta = d.meta or {}

        file_name = _normalize_text(meta.get("file_name") or "")
        title = _normalize_text(meta.get("title") or "")
        nav_path = _normalize_text(meta.get("nav_path") or "")
        source_url = _normalize_text(meta.get("source_url") or "")

        blob = f"{file_name} {title} {nav_path} {source_url}"
        score = float(getattr(d, "score", 0.0) or 0.0)

        score = _apply_pattern_boosts(
            score=score,
            blob=blob,
            file_name=file_name,
            title=title,
            source_url=source_url,
            patterns=normalized_patterns,
            strong_boost=strong_boost,
            weak_boost=weak_boost,
        )

        if component_variants:
            exact_component_hit = False

            for variant in component_variants:
                exact_file_candidates = {
                    f"{variant}.md",
                    f"{variant}.txt",
                    variant,
                }

                if file_name in exact_file_candidates:
                    score += exact_file_boost
                    exact_component_hit = True

                if title == variant:
                    score += exact_title_boost
                    exact_component_hit = True

                if source_url.endswith(f"/{variant}") or f"/{variant}#" in source_url:
                    score += exact_url_boost
                    exact_component_hit = True

                if variant in file_name:
                    score += component_file_boost

                if variant in title:
                    score += component_title_boost

                if variant in nav_path:
                    score += 0.55

                if variant in source_url:
                    score += 0.55

            if not exact_component_hit:
                if _looks_like_integration_doc(file_name, title, nav_path, source_url):
                    score -= integration_penalty

                if _looks_like_general_guide_doc(file_name, title, nav_path):
                    score -= guide_penalty

        d.score = score
        rescored.append(d)

    rescored.sort(
        key=lambda x: float(getattr(x, "score", 0.0) or 0.0),
        reverse=True,
    )
    return rescored