# chat/haystack_utils/tools/routing.py
import re
from typing import Optional, List
from haystack.dataclasses import Document

from .filters import filters_haystack, filters_user
from .formatters import dedupe, trim_docs
from ..document_store import document_store
from ..query_heuristics import normalize_query


def lex_score(query: str, text: str) -> int:
    q = (query or "").lower().strip()
    if not q:
        return 0

    tokens = [t for t in re.split(r"\W+", q) if len(t) >= 3]
    if not tokens:
        return 0

    hay = (text or "").lower()
    score = 0

    for t in tokens:
        score += hay.count(t)

    return score


def expand_symbol_aliases(query: str) -> str:
    q = normalize_query(query)

    replacements = {
        "chat message": "chatmessage",
        "tool invoker": "toolinvoker",
        "conditional router": "conditionalrouter",
        "prompt builder": "promptbuilder",
        "chat prompt builder": "chatpromptbuilder",
        "document writer": "documentwriter",
        "document store": "documentstore",
        "pg vector": "pgvector",
    }

    expanded = [q]

    for src, dst in replacements.items():
        if src in q and dst not in q:
            expanded.append(q.replace(src, dst))

    return " ".join(expanded)


def retrieve_reference_first(query: str, k: int, file_name: Optional[str] = None) -> List[Document]:
    ref_filters = filters_haystack(file_name=file_name, doc_type="reference")
    pool = document_store.filter_documents(filters=ref_filters)
    pool = dedupe(pool)

    if not (query or "").strip():
        return trim_docs(pool[:k])

    scored = []
    expanded_query = expand_symbol_aliases(query)
    qn = normalize_query(expanded_query)

    for d in pool:
        meta = d.meta or {}
        title = meta.get("title") or ""
        nav = meta.get("nav_path") or ""
        source_url = meta.get("source_url") or ""
        file_name_meta = meta.get("file_name") or ""
        content = d.content or ""

        file_name_meta_l = file_name_meta.lower()
        title_l = title.lower()
        nav_l = nav.lower()

        s = 0

        # Weighted lexical scoring by field importance
        s += 4 * lex_score(expanded_query, title)
        s += 4 * lex_score(expanded_query, file_name_meta)
        s += 3 * lex_score(expanded_query, nav)
        s += 2 * lex_score(expanded_query, source_url)
        s += 1 * lex_score(expanded_query, content)

        blob = f"{title}\n{nav}\n{source_url}\n{file_name_meta}\n{content}".lower()

        # Generic exact-ish symbol boosts
        if "chatmessage" in qn and "chatmessage" in blob:
            s += 8
        if "toolinvoker" in qn and "toolinvoker" in blob:
            s += 8
        if "conditionalrouter" in qn and "conditionalrouter" in blob:
            s += 8
        if "promptbuilder" in qn and "promptbuilder" in blob:
            s += 8
        if "chatpromptbuilder" in qn and "chatpromptbuilder" in blob:
            s += 8
        if "documentwriter" in qn and "documentwriter" in blob:
            s += 8

        if "agent" in qn and "agent" in blob:
            s += 3
        if "pipeline" in qn and "pipeline" in blob:
            s += 3
        if "tool" in qn and "tool" in blob:
            s += 2

        # Prefer more canonical docs over experimental pages for symbol questions
        if "experimental-" in file_name_meta_l:
            s -= 3

        # ChatMessage-specific tuning
        if "chatmessage" in qn:
            if "chatmessage" in file_name_meta_l or "chatmessage" in title_l:
                s += 10
            if "data-classes" in file_name_meta_l or "data-classes" in title_l or "data-classes" in nav_l:
                s += 6
            if "experimental-chatmessage-store" in file_name_meta_l:
                s -= 1  # keep it possible, but not dominant

        # ToolInvoker-specific tuning
        if "toolinvoker" in qn:
            if "toolinvoker" in file_name_meta_l or "toolinvoker" in title_l:
                s += 10
            if "tool-components" in file_name_meta_l:
                s += 4

        # ConditionalRouter-specific tuning
        if "conditionalrouter" in qn:
            if "conditionalrouter" in file_name_meta_l or "conditionalrouter" in title_l:
                s += 10
            if "routers-api" in file_name_meta_l:
                s += 4

        # PromptBuilder-specific tuning
        if "promptbuilder" in qn:
            if "promptbuilder" in file_name_meta_l or "promptbuilder" in title_l:
                s += 10
            if "builders-api" in file_name_meta_l:
                s += 4

        if "chatpromptbuilder" in qn:
            if "chatpromptbuilder" in file_name_meta_l or "chatpromptbuilder" in title_l:
                s += 10
            if "builders-api" in file_name_meta_l:
                s += 4

        if s > 0:
            scored.append((s, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = [d for _, d in scored[:k]]

    if not best:
        print("🟠 reference-first: 0 lexical hits → returning []")
        return []

    return trim_docs(best)


def filter_ragas_when_rag_query(query: str, docs: List[Document]) -> List[Document]:
    qn = normalize_query(query)
    is_rag_query = (qn == "rag") or qn.startswith("rag ")
    is_about_ragas = "ragas" in qn

    if not is_rag_query or is_about_ragas:
        return docs

    out: List[Document] = []
    for d in docs:
        m = d.meta or {}
        src = (m.get("source_url") or "").lower()
        fn = (m.get("file_name") or "").lower()
        title = (m.get("title") or "").lower()

        if "integrations-ragas" in src or "integrations-ragas" in fn:
            continue
        if "ragas" in title:
            continue

        out.append(d)

    return out


def file_exists_in_corpus(file_name: str, mode: str, user_id: Optional[str] = None) -> bool:
    if not file_name or not str(file_name).strip():
        return False

    fn = str(file_name).strip()
    mode = (mode or "haystack_docs").strip()

    if mode == "haystack":
        mode = "haystack_docs"
    if mode == "haystack_ref":
        mode = "haystack_reference"

    if mode == "user":
        if not user_id:
            return False
        f = filters_user(str(user_id), fn)
    elif mode == "haystack_reference":
        f = filters_haystack(file_name=fn, doc_type="reference")
    elif mode == "haystack_all":
        f = filters_haystack(file_name=fn, doc_type=None)
    else:
        f = filters_haystack(file_name=fn, doc_type="docs")

    docs = document_store.filter_documents(filters=f)
    return bool(docs)