import re
from typing import Optional, List, Dict, Any

from haystack.dataclasses import Document
from haystack.tools import Tool

from .settings import (
    client,
    OPENAI_CHAT_MODEL_QUIZ,
    OPENAI_TIMEOUT,
    QUIZ_TEMP,
    RETRIEVE_TOP_K,
)
from .retrieval import retrieve_documents


# ------------------------------
# Quiz generator helpers
# ------------------------------
def _looks_like_filename(s: str) -> bool:
    if not s:
        return False

    t = s.strip()
    if len(t) > 180:
        return False

    if re.search(r"\.(md|txt|pdf|docx)$", t, re.IGNORECASE):
        return True

    if ("/" in t or "\\" in t) and " " not in t:
        return True

    if " " not in t and re.fullmatch(r"[\w.\-()]+", t):
        return True

    return False


def _join_docs_content(docs: List[Document]) -> str:
    parts: List[str] = []
    for d in docs:
        c = (d.content or "").strip()
        if c:
            parts.append(c)
    return "\n\n".join(parts).strip()


def _fallback_quiz_markdown(text: str, n: int = 5) -> str:
    items = []

    for i in range(1, n + 1):
        items.append(
            f"""**{i}. Pytanie {i}?**  
a) Odpowiedź A  
b) Odpowiedź B  
c) Odpowiedź C  
d) Odpowiedź D"""
        )

    return "\n\n".join(items)


def _quiz_error_markdown(msg: str) -> str:
    safe = (msg or "").strip()
    return f"**Nie mogę wygenerować quizu.** {safe}"


def _docs_not_found_markdown(file_name: str) -> str:
    return _quiz_error_markdown(
        f"Nie znalazłem dokumentu `{file_name}` (albo nie ma w nim treści). "
        f"Podaj poprawną nazwę pliku (np. `tools-api.md`) albo wgraj dokument."
    )


# ------------------------------
# Quiz generator (Markdown only)
# ------------------------------
def generate_quiz(
    text: str = "",
    file_name: Optional[str] = None,
    query: str = "",
    top_k: int = RETRIEVE_TOP_K,
    mode: str = "haystack_all",
) -> Dict[str, Any]:
    """
    Generate quiz from:
    - explicit text, OR
    - file_name (fetch docs first), OR
    - short text that looks like a filename -> treated as file_name.

    Returns: {"quiz_questions_text": "<markdown>"}
    """
    raw_text = (text or "").strip()
    fn = (file_name or "").strip()
    q = (query or "").strip()
    k = int(top_k or RETRIEVE_TOP_K)

    if not fn and _looks_like_filename(raw_text):
        fn = raw_text
        raw_text = ""

    if fn:
        rr = retrieve_documents(
            query=q,
            top_k=k,
            file_name=fn,
            mode=mode,
        )
        docs = rr.get("documents", []) or []
        joined = _join_docs_content(docs)

        if joined:
            raw_text = joined
        else:
            print(
                f"\n📌 Tool: quiz_generator\n⚠️ No content found for file_name='{fn}' (mode={mode})."
            )
            return {"quiz_questions_text": _docs_not_found_markdown(fn)}

    if not raw_text:
        print(f"\n📌 Tool: quiz_generator\n⚠️ No text provided.")
        return {
            "quiz_questions_text": (
                '**Brak treści do quizu.** '
                'Wklej tekst po **"na podstawie:"** albo podaj poprawną nazwę pliku '
                '(np. `tools-api.md`).'
            )
        }

    if len(raw_text) < 200:
        print(f"\n📌 Tool: quiz_generator\n⚠️ Not enough text (len={len(raw_text)}), refusing.")
        return {
            "quiz_questions_text": _quiz_error_markdown(
                f"Za mało treści do sensownego quizu (len={len(raw_text)}). "
                "Podaj dłuższy fragment albo wskaż plik."
            )
        }

    print(
        f"\n📌 Tool: quiz_generator\n🔁 Params: text_len={len(raw_text)} "
        f"file_name='{fn}' query_len={len(q)} top_k={k} mode={mode}"
    )

    prompt = f"""
Na podstawie poniższego tekstu stwórz 5 pytań quizowych z czterema odpowiedziami.

Zwróć WYŁĄCZNIE czysty Markdown.
Bez HTML.
Bez ```.

Format DOKŁADNIE taki:

**1. Pytanie?**  
 a) Odpowiedź 1  
 b) Odpowiedź 2  
 c) Odpowiedź 3  
 d) Odpowiedź 4  

**2. Pytanie?**  
 a) Odpowiedź 1  
 b) Odpowiedź 2  
 c) Odpowiedź 3  
 d) Odpowiedź 4  

**3. Pytanie?**  
 a) Odpowiedź 1  
 b) Odpowiedź 2  
 c) Odpowiedź 3  
 d) Odpowiedź 4  

**4. Pytanie?**  
 a) Odpowiedź 1  
 b) Odpowiedź 2  
 c) Odpowiedź 3  
 d) Odpowiedź 4  

**5. Pytanie?**  
 a) Odpowiedź 1  
 b) Odpowiedź 2  
 c) Odpowiedź 3  
 d) Odpowiedź 4  

ZASADY:
- Dokładnie 5 pytań
- Każde pytanie w osobnym akapicie
- Odpowiedzi oznaczone a), b), c), d)
- Zachowaj dokładnie wcięcie przed odpowiedziami
- Nie podawaj poprawnych odpowiedzi
- Język: polski

Tekst źródłowy:
{raw_text}
""".strip()

    try:
        completion = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL_QUIZ,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jesteś generatorem quizów. "
                        "Zwracasz wyłącznie poprawny Markdown zgodny z instrukcją. "
                        "Nie używasz HTML. "
                        "Nie używasz code fences. "
                        "Zwracasz dokładnie 5 pytań z odpowiedziami a), b), c), d)."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=QUIZ_TEMP,
            timeout=OPENAI_TIMEOUT,
        )
        quiz_text = (completion.choices[0].message.content or "").strip()

        if quiz_text.startswith("```"):
            quiz_text = quiz_text.strip("`").strip()

        if not quiz_text:
            return {
                "quiz_questions_text": _quiz_error_markdown(
                    "Model zwrócił pustą odpowiedź. Spróbuj ponownie."
                )
            }

        return {"quiz_questions_text": quiz_text}

    except Exception as e:
        print(f"[QUIZ_TOOL ERROR] {e}")
        return {"quiz_questions_text": _fallback_quiz_markdown(raw_text)}


quiz_tool = Tool(
    name="quiz_generator",
    description=(
        "Generate quiz questions (Markdown) from provided text OR from a file_name "
        "(the tool will retrieve document content automatically)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Source text to generate quiz from (optional)."
            },
            "file_name": {
                "type": "string",
                "description": "Exact file name to base the quiz on (optional)."
            },
            "query": {
                "type": "string",
                "description": "Optional query to narrow retrieval within the file."
            },
            "top_k": {
                "type": "integer",
                "description": "How many chunks to retrieve if file_name is used."
            },
            "mode": {
                "type": "string",
                "enum": ["haystack_docs", "haystack_reference", "haystack_all", "user"],
                "description": "Corpus to search when retrieving by file_name."
            },
        },
        "required": []
    },
    function=generate_quiz,
    outputs_to_state={"quiz_questions_text": {"source": "quiz_questions_text"}}
)