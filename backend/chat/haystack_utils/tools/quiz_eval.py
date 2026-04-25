# chat/haystack_utils/tools/quiz_eval.py
import re
from typing import Dict, Any, List, Tuple

from haystack.tools import Tool
from bs4 import BeautifulSoup

from .settings import (
    client,
    OPENAI_CHAT_MODEL_EVAL,
    OPENAI_TIMEOUT,
)


# ------------------------------
# Helpers: answers normalization
# ------------------------------
def _normalize_user_answers(s: str) -> str:
    """
    Accepts formats like:
      - "1a 2b 3c 4d 5a"
      - "1.a 2.b 3.c 4.d 5.a"
      - with newlines etc.
    Returns: "1.a 2.b 3.c 4.d 5.a"
    """
    if not s:
        return ""

    t = s.strip().lower()
    t = t.replace("\n", " ").replace(",", " ").replace(";", " ")
    t = re.sub(r"\s+", " ", t).strip()

    # convert "1a" -> "1.a"
    t = re.sub(r"\b(\d{1,2})\s*([abcd])\b", r"\1.\2", t)

    t = re.sub(r"\s+", " ", t).strip()
    return t


# ------------------------------
# Helpers: parse quiz HTML
# ------------------------------
def _parse_quiz_html(html: str) -> List[Tuple[str, List[str]]]:
    """
    Backward-compatible parser for old quiz HTML.
    Supports both:
    1) old <ol><li>...</li></ol> structure
    2) current/fallback HTML with <div class="quiz-item"><p>...</p></div>
    """
    if not html or not isinstance(html, str):
        return []

    h = html.strip()
    if h.startswith("```"):
        h = h.strip("`").strip()

    soup = BeautifulSoup(h, "html.parser")
    items: List[Tuple[str, List[str]]] = []

    # Variant A: <ol><li>Question<ol type="a"><li>...</li></ol></li></ol>
    outer_ol = soup.find("ol")
    if outer_ol:
        for li in outer_ol.find_all("li", recursive=False):
            nested_ol = li.find("ol")
            if not nested_ol:
                continue

            question_parts = []
            for child in li.contents:
                if getattr(child, "name", None) == "ol":
                    break
                text = str(child).strip()
                if text:
                    question_parts.append(text)

            question = " ".join(question_parts)
            question = BeautifulSoup(question, "html.parser").get_text(" ", strip=True)
            question = re.sub(r"\s+", " ", question).strip()

            options: List[str] = []
            for opt_li in nested_ol.find_all("li", recursive=False)[:4]:
                option_text = opt_li.get_text(" ", strip=True)
                option_text = re.sub(r"\s+", " ", option_text).strip()
                if option_text:
                    options.append(option_text)

            if question and len(options) == 4:
                items.append((question, options))

            if len(items) >= 5:
                break

        if items:
            return items

    # Variant B: <div class="quiz-item"><p><strong>1. ...</strong></p><p>a) ...</p>...</div>
    quiz_items = soup.select("div.quiz-item")
    if quiz_items:
        for block in quiz_items[:5]:
            paragraphs = block.find_all("p", recursive=False)
            if not paragraphs:
                continue

            question = paragraphs[0].get_text(" ", strip=True)
            question = re.sub(r"^\d+\.\s*", "", question).strip()

            options: List[str] = []
            for p in paragraphs[1:]:
                txt = p.get_text(" ", strip=True)
                txt = re.sub(r"\s+", " ", txt).strip()
                if re.match(r"^[a-d]\)", txt, flags=re.IGNORECASE):
                    options.append(txt)

            if question and len(options) == 4:
                items.append((question, options))

        if items:
            return items

    return []


# ------------------------------
# Helpers: parse quiz Markdown
# ------------------------------
def _parse_quiz_markdown(text: str) -> List[Tuple[str, List[str]]]:
    """
    Parse markdown quiz in format:

    **1. Pytanie?**
    a) Odpowiedź 1
    b) Odpowiedź 2
    c) Odpowiedź 3
    d) Odpowiedź 4
    """
    if not text or not isinstance(text, str):
        return []

    src = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = [line.strip() for line in src.split("\n")]

    items: List[Tuple[str, List[str]]] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # Match: **1. Question?**
        m = re.match(r"^\*\*\s*(\d+)\.\s*(.+?)\s*\*\*$", line)
        if not m:
            i += 1
            continue

        question = m.group(2).strip()
        options: List[str] = []

        j = i + 1
        while j < n and len(options) < 4:
            candidate = lines[j]
            if re.match(r"^[a-d]\)\s+.+", candidate, flags=re.IGNORECASE):
                options.append(candidate)
            elif candidate == "":
                pass
            else:
                break
            j += 1

        if question and len(options) == 4:
            items.append((question, options))

        i = j

        if len(items) >= 5:
            break

    return items


def _parse_quiz_any(quiz_text: str) -> List[Tuple[str, List[str]]]:
    """
    Prefer markdown parsing for new quizzes,
    fallback to HTML parsing for old quizzes already stored in DB.
    """
    parsed_md = _parse_quiz_markdown(quiz_text)
    if parsed_md:
        return parsed_md

    parsed_html = _parse_quiz_html(quiz_text)
    if parsed_html:
        return parsed_html

    return []


def _build_eval_prompt(parsed: List[Tuple[str, List[str]]], user_answers: str) -> str:
    """
    Builds a short, stable prompt from parsed quiz.
    """
    lines = []
    for i, (q, opts) in enumerate(parsed, start=1):
        lines.append(f"{i}) {q}")
        lines.append(f"   a) {opts[0]}")
        lines.append(f"   b) {opts[1]}")
        lines.append(f"   c) {opts[2]}")
        lines.append(f"   d) {opts[3]}")
        lines.append("")

    quiz_text = "\n".join(lines).strip()

    return f"""
Quiz (pytania i odpowiedzi):
{quiz_text}

Odpowiedzi użytkownika:
{user_answers}

Zadanie:
- Dla każdego pytania wyznacz poprawną odpowiedź (a/b/c/d) na podstawie treści pytania i opcji.
- Porównaj z odpowiedzią użytkownika.
- Zwróć WYŁĄCZNIE tabelę w Markdown (bez ```markdown i bez żadnego tekstu przed/po):

| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |
|----|---------|---------------------|------------------------|-----|

Na końcu dodaj osobną linię (po tabeli):
**Wynik: X/5**
""".strip()


# ------------------------------
# OpenAI call with retry
# ------------------------------
def _eval_with_retry(messages, *, timeout: float) -> str:
    completion = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL_EVAL,
        messages=messages,
        temperature=0.0,
        timeout=timeout,
        max_tokens=900,
    )

    choice = completion.choices[0]
    content = (choice.message.content or "").strip()
    finish = getattr(choice, "finish_reason", None)

    if finish == "length":
        print("⚠️ quiz_evaluator: truncated output, retrying with more tokens")
        completion = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL_EVAL,
            messages=messages,
            temperature=0.0,
            timeout=timeout,
            max_tokens=1800,
        )
        content = (completion.choices[0].message.content or "").strip()

    if content.startswith("```"):
        content = content.strip("`").strip()

    return content


# ------------------------------
# Post-processing helpers
# ------------------------------
def _parse_eval_rows(result_text: str) -> List[Dict[str, str]]:
    """
    Parse rows from markdown table returned by the evaluator.

    Expected row format:
    | 1 | Pytanie | b | a | ✗ |
    """
    rows: List[Dict[str, str]] = []

    for line in (result_text or "").splitlines():
        stripped = line.strip()

        if not stripped.startswith("|"):
            continue
        if stripped.startswith("| Nr "):
            continue
        if stripped.startswith("|----"):
            continue
        if "Wynik:" in stripped:
            continue

        parts = [p.strip() for p in stripped.split("|")[1:-1]]
        if len(parts) != 5:
            continue

        nr, question, correct_answer, user_answer, mark = parts
        if not nr.isdigit():
            continue

        rows.append(
            {
                "nr": nr,
                "question": question,
                "correct_answer": correct_answer,
                "user_answer": user_answer,
                "mark": mark,
            }
        )

    return rows


def _strip_option_prefix(text: str) -> str:
    if not text:
        return text
    return re.sub(r"^[a-d]\)\s*", "", text.strip(), flags=re.IGNORECASE)


def _letter_to_option_text(options: List[str], letter: str) -> str:
    letter = (letter or "").strip().lower()
    idx_map = {"a": 0, "b": 1, "c": 2, "d": 3}
    idx = idx_map.get(letter)
    if idx is None or idx >= len(options):
        return "-"
    return _strip_option_prefix(options[idx])


def _build_enriched_rows(result_text: str, parsed_quiz: List[Tuple[str, List[str]]]) -> List[Dict[str, str]]:
    rows = _parse_eval_rows(result_text)
    enriched: List[Dict[str, str]] = []

    for row in rows:
        try:
            idx = int(row["nr"]) - 1
        except Exception:
            continue

        if not (0 <= idx < len(parsed_quiz)):
            continue

        question_text, options = parsed_quiz[idx]

        correct_letter = (row.get("correct_answer") or "").strip().lower()
        user_letter = (row.get("user_answer") or "").strip().lower()
        mark = (row.get("mark") or "").strip()

        correct_text = _letter_to_option_text(options, correct_letter)
        user_text = _letter_to_option_text(options, user_letter) if user_letter in {"a", "b", "c", "d"} else "-"

        enriched.append(
            {
                "nr": row["nr"],
                "question": question_text,
                "correct_letter": correct_letter or "-",
                "correct_text": correct_text,
                "user_letter": user_letter or "-",
                "user_text": user_text,
                "mark": mark,
            }
        )

    return enriched


def _build_final_result_markdown(result_text: str, parsed_quiz: List[Tuple[str, List[str]]]) -> str:
    enriched_rows = _build_enriched_rows(result_text, parsed_quiz)
    if not enriched_rows:
        return result_text

    score = sum(1 for row in enriched_rows if "✔" in row["mark"])
    total = len(enriched_rows)

    lines = []
    lines.append("| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |")
    lines.append("|----|---------|---------------------|------------------------|-----|")

    for row in enriched_rows:
        correct_display = f"{row['correct_letter']}) {row['correct_text']}"
        user_display = (
            f"{row['user_letter']}) {row['user_text']}"
            if row["user_letter"] in {"a", "b", "c", "d"}
            else "-"
        )

        lines.append(
            f"| {row['nr']} | {row['question']} | {correct_display} | {user_display} | {row['mark']} |"
        )

    lines.append("")
    lines.append(f"**Wynik: {score}/{total}**")

    return "\n".join(lines)


def _build_review_section(result_text: str, parsed_quiz: List[Tuple[str, List[str]]]) -> str:
    enriched_rows = _build_enriched_rows(result_text, parsed_quiz)
    if not enriched_rows:
        return ""

    mistakes = [row for row in enriched_rows if "✗" in row["mark"]]

    if not mistakes:
        return "\n\n## Podsumowanie\nBrawo — wszystkie odpowiedzi są poprawne."

    lines = []
    lines.append("\n\n## Podsumowanie braków")
    lines.append("Najwięcej problemu sprawiły Ci następujące zagadnienia:\n")

    for i, item in enumerate(mistakes, start=1):
        lines.append(
            f"{i}. **{item['question']}**\n"
            f"   - Twoja odpowiedź: **{item['user_letter']}) {item['user_text']}**\n"
            f"   - Poprawna odpowiedź: **{item['correct_letter']}) {item['correct_text']}**"
        )

    lines.append("\n## Do powtórki")
    for item in mistakes:
        lines.append(f"- {item['question']}")

    lines.append("\n## Rekomendacja")
    lines.append(
        "Przeczytaj jeszcze raz fragmenty dokumentacji związane z powyższymi pytaniami "
        "i spróbuj zrobić kolejny quiz tylko z tych zagadnień."
    )

    return "\n".join(lines)


# ------------------------------
# Tool function
# ------------------------------
def evaluate_quiz_answers(user_answers: str, quiz_questions_text: str) -> Dict[str, Any]:
    ua_norm = _normalize_user_answers(user_answers)
    ua_preview = (ua_norm or "")[:60].replace("\n", "\\n")

    parsed = _parse_quiz_any(quiz_questions_text)

    print(
        f"\n📌 Tool: quiz_evaluator\n"
        f"🔁 Params: user_answers='{ua_preview}...' parsed_questions={len(parsed)} "
        f"quiz_text_len={len(quiz_questions_text or '')}"
    )

    if len(parsed) < 5:
        return {
            "quiz_result": (
                "| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |\n"
                "|----|---------|---------------------|------------------------|-----|\n"
                "| 1  | (brak pełnego quizu do oceny) | - | - | ✗ |\n\n"
                "**Wynik: 0/5**"
            )
        }

    prompt = _build_eval_prompt(parsed, ua_norm)

    try:
        result = _eval_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jesteś ocenianiem quizu. "
                        "Zwracasz WYŁĄCZNIE tabelę Markdown + linię Wynik. "
                        "Nie używasz code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            timeout=OPENAI_TIMEOUT,
        )

        if not result:
            raise RuntimeError("Empty evaluation result")

        rebuilt_result = _build_final_result_markdown(result, parsed)
        review = _build_review_section(result, parsed)
        final_result = rebuilt_result + review

        return {"quiz_result": final_result}

    except Exception as e:
        print(f"[EVAL_TOOL ERROR] {e}")
        return {
            "quiz_result": (
                "| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |\n"
                "|----|---------|---------------------|------------------------|-----|\n"
                "| 1  | (błąd oceny) | - | - | ✗ |\n\n"
                "**Wynik: 0/5**"
            )
        }


evaluate_quiz_tool = Tool(
    name="quiz_evaluator",
    description="Evaluate user quiz answers against generated quiz content (Markdown or legacy HTML). Returns a Markdown table and score.",
    parameters={
        "type": "object",
        "properties": {
            "user_answers": {"type": "string", "description": "User answers (e.g., '1.a 2.b 3.c 4.d 5.a')"},
            "quiz_questions_text": {"type": "string", "description": "Quiz content from quiz_generator (Markdown or legacy HTML)."},
        },
        "required": ["user_answers", "quiz_questions_text"],
    },
    function=evaluate_quiz_answers,
)