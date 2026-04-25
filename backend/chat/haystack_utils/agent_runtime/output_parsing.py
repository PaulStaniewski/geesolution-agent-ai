# chat/haystack_utils/agent_runtime/output_parsing.py

import ast
import json


def collect_tool_names(obj) -> set[str]:
    """
    Best-effort extraction of tool names from agent output.
    Supports multiple Haystack output shapes.
    """
    names: set[str] = set()
    if obj is None:
        return names

    if isinstance(obj, dict):
        for key in ("tool_calls", "tools", "events", "trace", "tool_invocations"):
            if key in obj:
                names |= collect_tool_names(obj.get(key))
        names |= collect_tool_names(obj.get("messages"))
        return names

    if isinstance(obj, list):
        for item in obj:
            names |= collect_tool_names(item)
        return names

    for attr in ("tool_name", "name", "tool"):
        val = getattr(obj, attr, None)
        if isinstance(val, str) and val:
            names.add(val)

    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            names |= collect_tool_names(to_dict())
        except Exception:
            pass

    return names


def is_quiz_flow(output: dict) -> bool:
    """True if quiz tools were used."""
    tool_names = collect_tool_names(output)
    return ("quiz_generator" in tool_names) or ("quiz_evaluator" in tool_names)


def safe_parse_tool_result(s: str) -> dict:
    """
    ToolCallResult.result bywa stringiem w stylu "{'quiz_questions_text': '<ol>...</ol>'}"
    albo JSON. Parsujemy bezpiecznie.
    """
    if not s or not isinstance(s, str):
        return {}

    t = s.strip()

    # 1) JSON
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass

    # 2) Python dict repr (single quotes)
    try:
        obj = ast.literal_eval(t)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def extract_quiz_text_from_messages(msgs) -> str:
    """
    Szuka ToolCallResult i wyciąga quiz_questions_text / quiz_result.
    """
    if not msgs:
        return ""

    for m in reversed(msgs):
        # Haystack ChatMessage tool content często jest listą ToolCallResult w _content
        content = getattr(m, "_content", None) or getattr(m, "content", None)

        if isinstance(content, list):
            for item in content:
                # ToolCallResult ma .result (string)
                res = None
                if isinstance(item, dict):
                    res = item.get("result")
                else:
                    res = getattr(item, "result", None)

                if isinstance(res, str) and res.strip():
                    parsed = safe_parse_tool_result(res)
                    for key in ("quiz_result", "quiz_questions_text"):
                        v = parsed.get(key)
                        if isinstance(v, str) and v.strip():
                            return v.strip()

    return ""


def pick_final_text_from_output(output: dict) -> str:
    """
    1) Prefer state fields (quiz tools write there).
    2) Else: try extracting quiz text from TOOL messages (ToolCallResult.result).
    3) Else: take last assistant message (avoid TOOL ChatMessage stringification).
    """
    if not output:
        return ""

    # 1) Prefer state (because tools write outputs_to_state)
    state = output.get("state") or {}
    for key in ("quiz_result", "quiz_questions_text"):
        v = state.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()

    # 2) Try extract quiz payload from TOOL messages (ToolCallResult.result)
    msgs = output.get("messages") or []
    tool_txt = extract_quiz_text_from_messages(msgs)
    if tool_txt:
        return tool_txt

    # 3) Otherwise pick last assistant message from output messages
    for m in reversed(msgs):
        role = getattr(m, "_role", None) or getattr(m, "role", None) or getattr(m, "role_", None)
        role_str = str(role).lower() if role is not None else ""
        if "assistant" in role_str:
            txt = getattr(m, "content", None) or getattr(m, "text", None)
            if isinstance(txt, str) and txt.strip():
                return txt.strip()

    return ""