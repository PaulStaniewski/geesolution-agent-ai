# chat/haystack_utils/agent_runtime/constants.py

import os

SAFE_TAGS = [
    "p", "b", "i", "strong", "em", "code", "pre", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "blockquote", "a", "br", "table", "thead",
    "tbody", "tr", "th", "td"
]

SAFE_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "ol": ["type"],
}

HISTORY_LIMIT = int(os.getenv("STREAM_HISTORY_LIMIT", "10"))

SOURCES_PATTERNS = [
    r"\n\*\*Źródła\*\*[\s\S]*$",
    r"\nŹródła\s*:[\s\S]*$",
    r"\n\*\*Sources\*\*[\s\S]*$",
    r"\nSources\s*:[\s\S]*$",
]