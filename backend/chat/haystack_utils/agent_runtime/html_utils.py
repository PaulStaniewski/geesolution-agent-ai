# chat/haystack_utils/agent_runtime/html_utils.py

import re
import bleach

from .constants import SOURCES_PATTERNS


def strip_sources_block(text: str) -> str:
    """Remove a trailing Sources/Źródła section (only for quiz flows)."""
    if not text:
        return text

    out = text
    for pat in SOURCES_PATTERNS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return out.rstrip()


def md_fences_to_html(s: str) -> str:
    """
    Convert Markdown triple-backtick fences to HTML <pre><code>...</code></pre>
    before bleach sanitization.
    """
    return re.sub(
        r"```(\w+)?\n(.*?)```",
        lambda m: f"<pre><code>{bleach.clean(m.group(2), strip=False)}</code></pre>",
        s,
        flags=re.DOTALL
    )