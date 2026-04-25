from typing import Optional, List

from haystack.dataclasses import Document

from ...document_store import document_store
from ..formatters import dedupe
from .filters import filters_for_mode


def sort_full_file_docs(docs: List[Document]) -> List[Document]:
    """
    Stable ordering for full-file retrieval.
    Prefer explicit chunk/page metadata when available.
    """
    return sorted(
        docs,
        key=lambda d: (
            (d.meta or {}).get("page_number", 0),
            (d.meta or {}).get("chunk_index", 0),
            (d.meta or {}).get("split_id", 0),
            (d.meta or {}).get("position", 0),
        ),
    )


def retrieve_all_chunks_of_file(
    *,
    mode: str,
    file_name: str,
    user_id: Optional[str],
) -> List[Document]:
    """
    Fetch all chunks belonging to a single file using metadata filters only.
    No embedding / semantic ranking is used here.
    """
    filters = filters_for_mode(
        mode,
        user_id=user_id,
        file_name=file_name,
        doc_type=None,
    )

    docs = document_store.filter_documents(filters=filters)
    docs = dedupe(docs)
    docs = sort_full_file_docs(docs)
    return docs