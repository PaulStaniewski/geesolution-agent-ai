from typing import List, Optional

from haystack.dataclasses import Document

from ..formatters import trim_docs, dedupe
from ...query_heuristics import normalize_query
from ...document_store import document_store
from .filters import filters_for_mode


def debug_top_docs(docs: List[Document], limit: int = 5) -> None:
    out = []
    for d in docs[:limit]:
        m = d.meta or {}
        out.append(
            {
                "file_name": m.get("file_name"),
                "title": m.get("title"),
                "doc_type": m.get("doc_type"),
                "source_url": m.get("source_url"),
                "score": getattr(d, "score", None),
            }
        )
    print("📎 top docs:", out)


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _extract_doc_identity(doc: Document) -> str:
    meta = doc.meta or {}
    return (
        _normalize_text(meta.get("file_name") or "")
        or _normalize_text(meta.get("source_url") or "")
        or _normalize_text(meta.get("title") or "")
    )


def component_name_variants(component_name: Optional[str]) -> List[str]:
    name = _normalize_text(component_name or "")
    if not name:
        return []

    compact = name.replace(" ", "").replace("-", "").replace("_", "")
    dashed = name.replace(" ", "-").replace("_", "-")
    underscored = name.replace(" ", "_").replace("-", "_")

    variants = {name, compact, dashed, underscored}
    return [v for v in variants if v]


def _doc_matches_component(doc: Document, component_name: Optional[str]) -> bool:
    variants = component_name_variants(component_name)
    if not variants:
        return False

    meta = doc.meta or {}
    file_name = _normalize_text(meta.get("file_name") or "")
    title = _normalize_text(meta.get("title") or "")
    nav_path = _normalize_text(meta.get("nav_path") or "")
    source_url = _normalize_text(meta.get("source_url") or "")

    blob = f"{file_name} {title} {nav_path} {source_url}"

    for variant in variants:
        if not variant:
            continue

        if file_name == f"{variant}.md":
            return True
        if file_name == f"{variant}.txt":
            return True
        if file_name == variant:
            return True
        if title == variant:
            return True
        if source_url.endswith(f"/{variant}"):
            return True
        if f"/{variant}#" in source_url:
            return True
        if variant in blob:
            return True

    return False


def merge_doc_lists(
    *doc_lists: List[Document],
    k: int,
    preferred_component: Optional[str] = None,
) -> List[Document]:
    """
    Merge multiple retrieval result lists in a less naive way.

    Strategy:
    - dedupe all docs
    - if a preferred component is known, keep the strongest matching doc first
    - then fill the remaining slots by score
    """
    merged: List[Document] = []

    for lst in doc_lists:
        if lst:
            merged.extend(lst)

    merged = dedupe(merged)
    merged.sort(
        key=lambda x: float(getattr(x, "score", 0.0) or 0.0),
        reverse=True,
    )

    if not merged:
        return []

    selected: List[Document] = []
    selected_ids = set()

    if preferred_component:
        preferred_docs = [
            doc for doc in merged if _doc_matches_component(doc, preferred_component)
        ]
        preferred_docs.sort(
            key=lambda x: float(getattr(x, "score", 0.0) or 0.0),
            reverse=True,
        )

        if preferred_docs:
            top_preferred = preferred_docs[0]
            doc_id = _extract_doc_identity(top_preferred)
            if doc_id:
                selected.append(top_preferred)
                selected_ids.add(doc_id)

    for doc in merged:
        if len(selected) >= k:
            break

        doc_id = _extract_doc_identity(doc)
        if doc_id and doc_id in selected_ids:
            continue

        selected.append(doc)
        if doc_id:
            selected_ids.add(doc_id)

    selected = trim_docs(selected[:k])
    return selected


def find_component_docs(
    component_name: Optional[str],
    *,
    mode: str,
    user_id: Optional[str],
    file_name: Optional[str],
) -> List[Document]:
    """
    Hard-lookup helper for exact or near-exact component page discovery.

    This is used as a stronger fallback than pure embedding retrieval.
    """
    variants = component_name_variants(component_name)
    if not variants:
        return []

    base_filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type=None,
    )

    all_docs = document_store.filter_documents(filters=base_filters)
    if not all_docs:
        return []

    matched: List[Document] = []

    for doc in all_docs:
        meta = doc.meta or {}
        file_name_meta = _normalize_text(meta.get("file_name") or "")
        title_meta = _normalize_text(meta.get("title") or "")
        nav_path_meta = _normalize_text(meta.get("nav_path") or "")
        source_url_meta = _normalize_text(meta.get("source_url") or "")

        blob = f"{file_name_meta} {title_meta} {nav_path_meta} {source_url_meta}"

        for variant in variants:
            if (
                file_name_meta == f"{variant}.md"
                or file_name_meta == f"{variant}.txt"
                or file_name_meta == variant
                or title_meta == variant
                or source_url_meta.endswith(f"/{variant}")
                or f"/{variant}#" in source_url_meta
                or variant in blob
            ):
                matched.append(doc)
                break

    matched = dedupe(matched)
    matched.sort(
        key=lambda x: float(getattr(x, "score", 0.0) or 0.0),
        reverse=True,
    )
    return matched


def extract_integration_keywords(query: str) -> List[str]:
    qn = normalize_query(query)

    known = [
        "pgvector",
        "weaviate",
        "qdrant",
        "pinecone",
        "ollama",
        "openrouter",
        "openai",
        "anthropic",
        "mistral",
        "chroma",
        "elasticsearch",
        "opensearch",
        "faiss",
        "mongodb",
        "vertex",
        "bedrock",
        "cohere",
        "watsonx",
    ]

    return [name for name in known if name in qn]