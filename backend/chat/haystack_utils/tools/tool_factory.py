from typing import Optional
from haystack.tools import Tool

from .settings import RETRIEVE_TOP_K, DEFAULT_RETRIEVE_MODE
from .retrieval import retrieve_documents


def document_tool_for(
    user_id: Optional[str] = None,
    mode: Optional[str] = None,
    default_mode: Optional[str] = None,
    name: Optional[str] = None,
) -> Tool:
    use_mode = (mode or default_mode or DEFAULT_RETRIEVE_MODE).strip()

    if use_mode == "haystack":
        use_mode = "haystack_docs"
    if use_mode == "haystack_ref":
        use_mode = "haystack_reference"

    tool_name = name or "document_retriever"

    def _fn(
        query: str = "",
        top_k: int = RETRIEVE_TOP_K,
        file_name: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        allowed = ("haystack_docs", "haystack_reference", "haystack_all", "user")
        the_mode = (mode.strip() if isinstance(mode, str) else None)

        if name is None and the_mode in allowed:
            final_mode = the_mode
        else:
            final_mode = use_mode

        return retrieve_documents(
            query=query,
            user_id=str(user_id) if user_id is not None else None,
            top_k=top_k,
            file_name=file_name,
            mode=final_mode,
        )

    base_props = {
        "query": {
            "type": "string",
            "description": (
                "User question or search query describing what should be found "
                "in the documentation."
            ),
        },
        "file_name": {
            "type": "string",
            "description": (
                "Exact file name to restrict the search to one document, if known."
            ),
        },
        "top_k": {
            "type": "integer",
            "description": "Maximum number of relevant results to return.",
        },
    }

    if name is None:
        base_props["mode"] = {
            "type": "string",
            "enum": ["haystack_docs", "haystack_reference", "haystack_all", "user"],
            "description": (
                "Which corpus to search: concept docs, API reference, all Haystack docs, "
                "or user documents."
            ),
        }

    if use_mode in ("haystack_docs", "haystack_reference", "haystack_all"):
        description = (
            "Use this tool when you need grounded information from Haystack documentation. "
            "Use it for definitions, explanations of how components work, differences between concepts, "
            "API-related questions, pipeline flow, agents, tools, retrievers, generators, and integrations. "
            "It returns relevant documentation fragments with metadata such as file name, title, section, score, "
            "and source URL. Do not use it for small talk or when the answer is already fully available in the current context."
        )
    else:
        description = (
            "Use this tool when you need grounded information from the user's uploaded documents. "
            "It returns relevant document fragments with metadata. Do not use it for small talk "
            "or when the answer is already fully available in the current context."
        )

    if name is None:
        description += (
            " You can choose the search corpus with the 'mode' parameter."
        )

    return Tool(
        name=tool_name,
        description=description,
        parameters={"type": "object", "properties": base_props},
        function=_fn,
        outputs_to_state={"retrieved_docs": {"source": "documents"}},
    )