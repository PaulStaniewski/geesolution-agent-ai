from typing import List, TypedDict
from haystack.dataclasses import Document

class RetrieverResult(TypedDict):
    documents: List[Document]
    context_text: str