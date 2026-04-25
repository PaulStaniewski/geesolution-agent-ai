# chat/haystack_utils/agent_runtime/quiz_utils.py

import re


def filename_candidates(token: str) -> list[str]:
    """
    Try a few variants to survive inconsistent storage:
    - with extension
    - without extension
    - add .md if missing
    """
    if not token:
        return []

    t = token.strip().strip("\"'“”")
    t = t.strip().strip(",.?!;:)")

    cands: list[str] = []
    cands.append(t)

    # If endswith .md -> add version without .md
    if t.lower().endswith(".md"):
        cands.append(t[:-3])
    else:
        # If no extension, add .md
        if not re.search(r"\.(md|txt|pdf|docx)$", t, re.IGNORECASE):
            cands.append(t + ".md")

    # de-dupe preserving order
    out: list[str] = []
    for x in cands:
        if x and x not in out:
            out.append(x)
    return out


def looks_like_not_found_html(html: str) -> bool:
    if not html:
        return True
    low = html.lower()
    return ("nie znalazłem dokumentu" in low) or ("brak treści do quizu" in low)