from typing import Optional, Dict, Any

from ..filters import filters_haystack, filters_user


def filters_for_mode(
    mode: str,
    *,
    user_id: Optional[str],
    file_name: Optional[str],
    doc_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build filters consistently for the selected retrieval scope.

    Rules:
    - mode='user' -> always stay inside current user's uploaded documents
    - haystack_*  -> only Haystack docs/reference scopes
    """
    if mode == "user":
        if not user_id:
            raise ValueError("user_id is required for mode='user'")
        return filters_user(str(user_id), file_name)

    if mode == "haystack_reference":
        return filters_haystack(file_name=file_name, doc_type="reference")

    if mode == "haystack_all":
        return filters_haystack(file_name=file_name, doc_type=None)

    # default -> haystack docs
    return filters_haystack(file_name=file_name, doc_type=doc_type or "docs")