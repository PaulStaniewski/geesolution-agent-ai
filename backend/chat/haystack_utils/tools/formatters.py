from typing import List
from haystack.dataclasses import Document
from .settings import MAX_CONTENT


def trim_docs(docs: List[Document], max_chars: int = MAX_CONTENT) -> List[Document]:
    out: List[Document] = []
    for d in docs:
        out.append(
            Document(
                id=getattr(d, "id", None),
                content=(d.content or "")[:max_chars],
                meta=dict(d.meta or {}),
                score=getattr(d, "score", None),
            )
        )
    return out


def dedupe(docs: List[Document]) -> List[Document]:
    seen = set()
    out = []

    for d in docs:
        m = d.meta or {}

        source_url = m.get("source_url") or ""
        file_name = m.get("file_name") or ""
        anchor = m.get("anchor") or m.get("section") or ""
        chunk_index = m.get("chunk_index")
        content_prefix = (d.content or "").strip()[:120]

        # Prefer semantic/location-based dedupe over raw chunk-based dedupe
        if source_url and anchor:
            key = ("url+anchor", source_url, anchor)
        elif file_name and anchor:
            key = ("file+anchor", file_name, anchor)
        elif source_url and chunk_index is not None:
            key = ("url+chunk", source_url, chunk_index)
        elif file_name and chunk_index is not None:
            key = ("file+chunk", file_name, chunk_index)
        else:
            key = ("content", content_prefix)

        if key in seen:
            continue

        seen.add(key)
        out.append(d)

    return out

def get_source_label(meta: dict) -> str:
    corpus = meta.get("corpus")
    source_url = meta.get("source_url")
    file_name = meta.get("file_name")

    if corpus == "user":
        return file_name or "uploaded document"

    return source_url or file_name or "unknown source"


def format_docs_for_llm(docs: List[Document]) -> str:
    blocks = []

    for i, d in enumerate(docs, start=1):
        meta = d.meta or {}

        title = (
            meta.get("title")
            or meta.get("nav_path")
            or meta.get("nav_level_3")
            or meta.get("file_name")
            or f"Document {i}"
        )

        source = get_source_label(meta)

        chunk_idx = meta.get("chunk_index", i - 1)
        doc_type = meta.get("doc_type") or "unknown"

        header_lines = [
            f"Document {i}",
            f"Title: {title}",
            f"Type: {doc_type}",
            f"Chunk: {chunk_idx}",
            f"Source: {source}",
        ]

        header = "\n".join(header_lines)
        content = d.content or ""

        blocks.append(f"{header}\n\nContent:\n\n{content}")

    return "\n\n---\n\n".join(blocks)