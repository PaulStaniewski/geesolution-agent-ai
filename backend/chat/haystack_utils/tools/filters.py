from typing import Optional, Dict, Any

def F_EQ(field: str, value):
    return {"field": field, "operator": "==", "value": value}

def F_AND(*conds):
    return {"operator": "AND", "conditions": list(conds)}

def filters_haystack(
    file_name: Optional[str] = None,
    doc_type: Optional[str] = "docs", 
) -> Dict[str, Any]:
    base = [F_EQ("meta.corpus", "haystack")]
    if doc_type:
        base.append(F_EQ("meta.doc_type", doc_type))
    if file_name and file_name.strip():
        base.append(F_EQ("meta.file_name", file_name.strip()))
    return F_AND(*base)

def filters_user(user_id: str, file_name: Optional[str]) -> Dict[str, Any]:
    conds = [
        F_EQ("meta.corpus", "user"),
        F_EQ("meta.namespace", f"user:{user_id}"),
    ]
    if file_name and file_name.strip():
        conds.append(F_EQ("meta.file_name", file_name.strip()))
    return F_AND(*conds)