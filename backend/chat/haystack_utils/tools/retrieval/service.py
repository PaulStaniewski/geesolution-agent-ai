from time import perf_counter
from typing import Optional, List, Dict, Any

from haystack.dataclasses import Document
from haystack_integrations.components.retrievers.pgvector import PgvectorEmbeddingRetriever

from chat.haystack_utils.embedder import embed_text
from ...document_store import document_store

from ..settings import RETRIEVE_TOP_K, DEFAULT_RETRIEVE_MODE
from ..types import RetrieverResult
from ..guards import (
    get_retriever_calls,
    inc_retriever_calls,
    get_last_retriever_result,
    set_last_retriever_result,
)
from ..formatters import trim_docs, dedupe, format_docs_for_llm
from ..routing import (
    retrieve_reference_first,
    filter_ragas_when_rag_query,
    file_exists_in_corpus,
)
from ...query_heuristics import (
    normalize_query,
    looks_like_conceptual_question,
    looks_like_reference_query,
    extract_component_name,
)

from .filters import filters_for_mode
from .helpers import debug_top_docs
from .full_file import retrieve_all_chunks_of_file
from .strategies import (
    run_comparison_strategy,
    run_guide_strategy,
    run_integration_strategy,
    run_architecture_strategy,
    run_troubleshooting_strategy,
    run_component_api_strategy,
)


def retrieve_documents(
    query: str = "",
    user_id: Optional[str] = None,
    top_k: int = RETRIEVE_TOP_K,
    file_name: Optional[str] = None,
    mode: str = DEFAULT_RETRIEVE_MODE,
    doc_query_type: Optional[str] = None,
    full_file_mode: bool = False,
) -> RetrieverResult:
    t0 = perf_counter()

    calls = get_retriever_calls()
    if calls >= 1:
        cached = get_last_retriever_result()
        if cached is not None:
            print("🟡 retriever: second call → returning cached result")
            return cached
        print("⛔ retriever: second call skipped (no cache)")
        return {"documents": [], "context_text": ""}

    inc_retriever_calls()

    q = (query or "").strip()
    k = int(top_k or RETRIEVE_TOP_K)
    qn = normalize_query(q)

    is_rag_query = (qn == "rag") or qn.startswith("rag ")
    is_about_ragas = "ragas" in qn

    mode = (mode or "haystack_docs").strip()
    if mode == "haystack":
        mode = "haystack_docs"
    if mode == "haystack_ref":
        mode = "haystack_reference"

    filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type="docs",
    )

    if file_name and str(file_name).strip():
        exists = file_exists_in_corpus(str(file_name).strip(), mode, user_id=user_id)
        if not exists:
            msg = f"NO_FILE_MATCH: '{str(file_name).strip()}' (mode={mode})"
            print(f"⛔ retriever: {msg}")
            result = {"documents": [], "context_text": msg}
            set_last_retriever_result(result)
            return result

    if full_file_mode and file_name:
        docs = retrieve_all_chunks_of_file(
            mode=mode,
            file_name=file_name,
            user_id=user_id,
        )

        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)

        print(
            f"📌 retriever(full-file) → {len(docs)} docs in {dt} ms | "
            f"mode={mode} | file_name={file_name!r}"
        )

        if docs:
            debug_top_docs(docs)

        result = {"documents": docs, "context_text": context_text}
        set_last_retriever_result(result)
        return result

    if not q and file_name:
        docs = document_store.filter_documents(filters=filters)
        docs = dedupe(docs)
        docs = trim_docs(docs[:k])
        context_text = format_docs_for_llm(docs)
        dt = int((perf_counter() - t0) * 1000)
        print(
            f"📌 retriever(file-only) → {len(docs)} docs in {dt} ms | "
            f"mode={mode} | file_name={file_name!r}"
        )
        result = {"documents": docs, "context_text": context_text}
        set_last_retriever_result(result)
        return result

    docs: List[Document] = []
    looks_ref = False
    is_conceptual = False

    def run_embedding(
        query_text: str,
        _filters: Dict[str, Any],
        *,
        pool_k: Optional[int] = None,
    ) -> List[Document]:
        q_emb = embed_text(query_text)
        emb_ret = PgvectorEmbeddingRetriever(
            document_store=document_store,
            top_k=pool_k or k,
            filters=_filters,
        )
        res = emb_ret.run(query_embedding=q_emb)
        return res.get("documents", []) if isinstance(res, dict) else []

    def docs_contain_component_match(
        documents: List[Document],
        component_name: Optional[str],
    ) -> bool:
        name = (component_name or "").strip().lower()
        if not name:
            return False

        compact = name.replace(" ", "").replace("-", "").replace("_", "")
        dashed = name.replace(" ", "-").replace("_", "-")
        underscored = name.replace(" ", "_").replace("-", "_")
        variants = {name, compact, dashed, underscored}

        for d in documents:
            meta = d.meta or {}
            file_name_local = (meta.get("file_name") or "").lower()
            title_local = (meta.get("title") or "").lower()
            nav_path_local = (meta.get("nav_path") or "").lower()
            source_url_local = (meta.get("source_url") or "").lower()

            blob = f"{file_name_local} {title_local} {nav_path_local} {source_url_local}"

            for variant in variants:
                if not variant:
                    continue
                if (
                    file_name_local == f"{variant}.md"
                    or title_local == variant
                    or source_url_local.endswith(f"/{variant}")
                    or variant in blob
                ):
                    return True

        return False

    if mode == "user":
        if not user_id:
            raise ValueError("user_id is required for mode='user'")

        if q:
            docs = run_embedding(q, filters)
        else:
            docs = document_store.filter_documents(filters=filters)

        docs = dedupe(docs)
        trimmed = trim_docs(docs[:k])

        if trimmed:
            debug_top_docs(trimmed)

        context_text = format_docs_for_llm(trimmed)
        dt = int((perf_counter() - t0) * 1000)
        print(
            f"📌 retriever(user-scope) → {len(trimmed)} docs in {dt} ms | "
            f"user_id={user_id!r} | file_name={file_name!r}"
        )

        result = {"documents": trimmed, "context_text": context_text}
        set_last_retriever_result(result)
        return result

    if q:
        looks_ref = looks_like_reference_query(q)
        is_conceptual = looks_like_conceptual_question(q)
        query_type = doc_query_type

        wants_ref = (
            mode == "haystack_reference"
            or (
                mode in ("haystack_all", "haystack_docs")
                and looks_ref
                and not is_conceptual
            )
        )

        if is_rag_query and not is_about_ragas:
            wants_ref = False

        print(
            f"🧭 ref_router: wants_ref={wants_ref} mode={mode} "
            f"looks_ref={looks_ref} is_conceptual={is_conceptual}"
        )
        print("🧭 ref_router:", {"query": q, "doc_query_type": query_type})

        strategy_result = None

        if query_type == "comparison":
            strategy_result = run_comparison_strategy(
                q=q,
                k=k,
                mode=mode,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        elif query_type == "guide_how_to":
            strategy_result = run_guide_strategy(
                q=q,
                k=k,
                mode=mode,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        elif query_type == "integration":
            strategy_result = run_integration_strategy(
                q=q,
                k=k,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        elif query_type == "architecture_workflow":
            strategy_result = run_architecture_strategy(
                q=q,
                k=k,
                mode=mode,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        elif query_type == "troubleshooting":
            strategy_result = run_troubleshooting_strategy(
                q=q,
                k=k,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        elif query_type == "component_api":
            strategy_result = run_component_api_strategy(
                q=q,
                k=k,
                mode=mode,
                user_id=user_id,
                file_name=file_name,
                run_embedding=run_embedding,
                t0=t0,
            )

        if strategy_result is not None:
            set_last_retriever_result(strategy_result)
            return strategy_result

        if is_conceptual and mode in ("haystack_all", "haystack_docs"):
            concept_filters = filters_for_mode(
                mode,
                user_id=user_id,
                file_name=file_name,
                doc_type="docs",
            )
            docs = run_embedding(q, concept_filters)
            docs = filter_ragas_when_rag_query(q, docs)

            if not docs and mode == "haystack_all":
                fallback_filters = filters_for_mode(
                    "haystack_all",
                    user_id=user_id,
                    file_name=file_name,
                    doc_type=None,
                )
                docs = run_embedding(q, fallback_filters)
                docs = filter_ragas_when_rag_query(q, docs)

            if not docs:
                print("🧯 conceptual fallback: 0 docs from docs-first → trying reference-first")
                ref_docs = retrieve_reference_first(query=q, k=k, file_name=file_name)
                if ref_docs:
                    docs = ref_docs

            component_name = extract_component_name(q)

            if component_name and not docs_contain_component_match(docs, component_name):
                print(
                    f"🛟 component rescue: conceptual query looks like component "
                    f"but no strong component match found → trying component_api strategy "
                    f"({component_name})"
                )

                rescue_result = run_component_api_strategy(
                    q=q,
                    k=k,
                    mode=mode,
                    user_id=user_id,
                    file_name=file_name,
                    run_embedding=run_embedding,
                    t0=t0,
                )

                if rescue_result is not None:
                    set_last_retriever_result(rescue_result)
                    return rescue_result

        elif wants_ref:
            ref_docs = retrieve_reference_first(query=q, k=k, file_name=file_name)
            if ref_docs:
                trimmed = trim_docs(ref_docs[:k])
                dt = int((perf_counter() - t0) * 1000)
                print(f"📌 retriever(hybrid:reference-first) → {len(trimmed)} docs in {dt} ms")
                debug_top_docs(trimmed)
                result = {
                    "documents": trimmed,
                    "context_text": format_docs_for_llm(trimmed),
                }
                set_last_retriever_result(result)
                return result

            if mode == "haystack_reference":
                docs = run_embedding(q, filters)
            else:
                fallback_filters = filters_for_mode(
                    "haystack_all",
                    user_id=user_id,
                    file_name=file_name,
                    doc_type=None,
                )
                docs = run_embedding(q, fallback_filters)
                docs = filter_ragas_when_rag_query(q, docs)

        else:
            docs = run_embedding(q, filters)
            docs = filter_ragas_when_rag_query(q, docs)

            if not docs and mode in ("haystack_all", "haystack_docs"):
                print("🧯 fallback: 0 docs from embedding → trying reference-first")
                ref_docs = retrieve_reference_first(query=q, k=k, file_name=file_name)
                if ref_docs:
                    docs = ref_docs

    docs = dedupe(docs)
    trimmed = trim_docs(docs[:k])

    if trimmed:
        debug_top_docs(trimmed)

    context_text = format_docs_for_llm(trimmed)
    dt = int((perf_counter() - t0) * 1000)
    print(
        f"📌 retriever(query) → {len(trimmed)} docs in {dt} ms | "
        f"mode={mode} | looks_ref={looks_ref if q else None} | "
        f"is_conceptual={is_conceptual if q else None} | "
        f"doc_query_type={doc_query_type!r} | file_name={file_name!r} | "
        f"full_file_mode={full_file_mode}"
    )

    result = {"documents": trimmed, "context_text": context_text}
    set_last_retriever_result(result)
    return result