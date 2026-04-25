from time import perf_counter
from typing import Optional

from haystack.dataclasses import Document

from ..formatters import trim_docs, dedupe, format_docs_for_llm
from ..routing import retrieve_reference_first, filter_ragas_when_rag_query
from .filters import filters_for_mode
from .helpers import (
    debug_top_docs,
    merge_doc_lists,
    extract_integration_keywords,
    find_component_docs,
)
from .scoring import boost_by_filename_patterns
from ...query_heuristics import extract_component_name, extract_comparison_component_names


def run_comparison_strategy(
    *,
    q: str,
    k: int,
    mode: str,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    docs_filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type="docs",
    )

    pool_k = max(k * 4, 16)

    comparison_components = extract_comparison_component_names(q)
    primary_component = comparison_components[0] if comparison_components else extract_component_name(q)

    comparison_patterns = list(comparison_components)
    if not comparison_patterns and primary_component:
        comparison_patterns = [primary_component]

    direct_docs_all = []
    for component in comparison_components[:2]:
        component_docs = find_component_docs(
            component,
            mode=mode,
            user_id=user_id,
            file_name=file_name,
        )
        if component_docs:
            component_docs = boost_by_filename_patterns(
                component_docs,
                comparison_patterns,
                query=q,
                component_name=component,
                component_file_boost=1.40,
                component_title_boost=1.10,
                strong_boost=0.50,
                weak_boost=0.15,
            )
            direct_docs_all.extend(component_docs)

    docs_docs = run_embedding(q, docs_filters, pool_k=pool_k)
    docs_docs = filter_ragas_when_rag_query(q, docs_docs)
    docs_docs = boost_by_filename_patterns(
        docs_docs,
        comparison_patterns,
        query=q,
        component_name=primary_component,
        component_file_boost=0.95,
        component_title_boost=0.75,
        strong_boost=0.40,
        weak_boost=0.12,
    )

    ref_docs = retrieve_reference_first(
        query=q,
        k=max(pool_k, 8),
        file_name=file_name,
    )

    ref_docs = boost_by_filename_patterns(
        ref_docs,
        comparison_patterns,
        query=q,
        component_name=primary_component,
        component_file_boost=1.10,
        component_title_boost=0.90,
        strong_boost=0.45,
        weak_boost=0.14,
    )

    docs = merge_doc_lists(
        direct_docs_all,
        docs_docs,
        ref_docs,
        k=max(k * 2, 8),
        preferred_component=primary_component,
    )

    if comparison_components:
        ensured = []
        used_ids = set()

        def _doc_id(doc: Document) -> str:
            meta = doc.meta or {}
            return (
                (meta.get("file_name") or "").lower()
                or (meta.get("source_url") or "").lower()
                or (meta.get("title") or "").lower()
            )

        for component in comparison_components[:2]:
            component_candidates = [
                doc for doc in docs
                if component in (
                    f"{(doc.meta or {}).get('file_name', '')} "
                    f"{(doc.meta or {}).get('title', '')} "
                    f"{(doc.meta or {}).get('source_url', '')}"
                ).lower()
            ]
            component_candidates.sort(
                key=lambda x: float(getattr(x, "score", 0.0) or 0.0),
                reverse=True,
            )

            if component_candidates:
                best = component_candidates[0]
                best_id = _doc_id(best)
                if best_id and best_id not in used_ids:
                    ensured.append(best)
                    used_ids.add(best_id)

        for doc in docs:
            if len(ensured) >= k:
                break

            doc_id = _doc_id(doc)
            if doc_id and doc_id in used_ids:
                continue

            ensured.append(doc)
            if doc_id:
                used_ids.add(doc_id)

        docs = ensured[:k]
    else:
        docs = docs[:k]

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(
            f"📌 retriever(comparison:entity-aware) → {len(docs)} docs in {dt} ms | "
            f"components={comparison_components}"
        )
        return {"documents": docs, "context_text": context_text}

    return None


def run_guide_strategy(
    *,
    q: str,
    k: int,
    mode: str,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    docs_filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type="docs",
    )
    docs_docs = run_embedding(q, docs_filters)
    docs_docs = filter_ragas_when_rag_query(q, docs_docs)
    docs_docs = boost_by_filename_patterns(
        docs_docs,
        ["creating-", "choosing-", "advanced-", "smart-", "function-", "debugging-"],
    )

    ref_docs = retrieve_reference_first(
        query=q,
        k=max(3, k // 2),
        file_name=file_name,
    )

    docs = merge_doc_lists(docs_docs, ref_docs, k=k)

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(f"📌 retriever(guide:mixed) → {len(docs)} docs in {dt} ms")
        return {"documents": docs, "context_text": context_text}

    return None


def run_integration_strategy(
    *,
    q: str,
    k: int,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    all_filters = filters_for_mode(
        "haystack_all",
        user_id=user_id,
        file_name=file_name,
        doc_type=None,
    )

    integration_pool_k = max(k * 3, 20)

    docs_all = run_embedding(q, all_filters, pool_k=integration_pool_k)
    docs_all = filter_ragas_when_rag_query(q, docs_all)

    integration_keywords = extract_integration_keywords(q)

    docs_all = boost_by_filename_patterns(
        docs_all,
        [
            *integration_keywords,
            "integrations-",
            "documentstore",
            "retriever",
            "generator",
            "embedder",
        ],
        strong_boost=0.80,
        weak_boost=0.20,
    )

    ref_docs = retrieve_reference_first(
        query=q,
        k=max(4, k),
        file_name=file_name,
    )

    ref_docs = boost_by_filename_patterns(
        ref_docs,
        [
            *integration_keywords,
            "documentstore",
            "retriever",
            "generator",
            "embedder",
        ],
        strong_boost=0.40,
        weak_boost=0.10,
    )

    docs = merge_doc_lists(docs_all, ref_docs, k=integration_pool_k)
    docs = dedupe(docs)
    docs = trim_docs(docs[:k])

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(f"📌 retriever(integration:mixed) → {len(docs)} docs in {dt} ms")
        return {"documents": docs, "context_text": context_text}

    return None


def run_architecture_strategy(
    *,
    q: str,
    k: int,
    mode: str,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    docs_filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type="docs",
    )
    docs_docs = run_embedding(q, docs_filters)
    docs_docs = filter_ragas_when_rag_query(q, docs_docs)
    docs_docs = boost_by_filename_patterns(
        docs_docs,
        ["advanced-", "creating-", "smart-", "pipelines", "agents", "components", "function-"],
    )

    ref_docs = retrieve_reference_first(
        query=q,
        k=max(2, k // 3),
        file_name=file_name,
    )

    docs = merge_doc_lists(docs_docs, ref_docs, k=k)

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(f"📌 retriever(architecture:mixed) → {len(docs)} docs in {dt} ms")
        return {"documents": docs, "context_text": context_text}

    return None


def run_troubleshooting_strategy(
    *,
    q: str,
    k: int,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    all_filters = filters_for_mode(
        "haystack_all",
        user_id=user_id,
        file_name=file_name,
        doc_type=None,
    )
    docs_all = run_embedding(q, all_filters)
    docs_all = filter_ragas_when_rag_query(q, docs_all)
    docs_all = boost_by_filename_patterns(
        docs_all,
        ["debugging-", "advanced-", "evaluation", "evaluators", "tracing", "logging", "hyde", "metadata-"],
    )

    ref_docs = retrieve_reference_first(
        query=q,
        k=max(2, k // 3),
        file_name=file_name,
    )

    docs = merge_doc_lists(docs_all, ref_docs, k=k)

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(f"📌 retriever(troubleshooting:mixed) → {len(docs)} docs in {dt} ms")
        return {"documents": docs, "context_text": context_text}

    return None


def run_component_api_strategy(
    *,
    q: str,
    k: int,
    mode: str,
    user_id: Optional[str],
    file_name: Optional[str],
    run_embedding,
    t0: float,
):
    component_name = extract_component_name(q)

    component_patterns = ["data-classes", "document", "answer"]
    if component_name:
        component_patterns = [component_name, *component_patterns]

    pool_k = max(k * 3, 12)

    direct_component_docs = find_component_docs(
        component_name,
        mode=mode,
        user_id=user_id,
        file_name=file_name,
    )

    if direct_component_docs:
        direct_component_docs = boost_by_filename_patterns(
            direct_component_docs,
            component_patterns,
            query=q,
            component_name=component_name,
            component_file_boost=1.40,
            component_title_boost=1.10,
            strong_boost=0.50,
            weak_boost=0.15,
        )

    ref_docs = retrieve_reference_first(
        query=q,
        k=pool_k,
        file_name=file_name,
    )

    if ref_docs:
        ref_docs = boost_by_filename_patterns(
            ref_docs,
            component_patterns,
            query=q,
            component_name=component_name,
            component_file_boost=1.10,
            component_title_boost=0.90,
            strong_boost=0.45,
            weak_boost=0.14,
        )

    docs_filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type="docs",
    )
    docs_docs = run_embedding(q, docs_filters, pool_k=pool_k)
    docs_docs = filter_ragas_when_rag_query(q, docs_docs)
    docs_docs = boost_by_filename_patterns(
        docs_docs,
        component_patterns,
        query=q,
        component_name=component_name,
        component_file_boost=0.95,
        component_title_boost=0.75,
        strong_boost=0.40,
        weak_boost=0.12,
    )

    docs = merge_doc_lists(
        direct_component_docs,
        docs_docs,
        ref_docs,
        k=k,
        preferred_component=component_name,
    )

    if docs:
        debug_top_docs(docs)
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(f"📌 retriever(component_api:mixed) → {len(docs)} docs in {dt} ms")
        return {"documents": docs, "context_text": context_text}

    return None