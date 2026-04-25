# chat/haystack_utils/agent_runtime/execution.py

import asyncio, re
from typing import List

from asgiref.sync import sync_to_async
from django.utils import timezone
from haystack.dataclasses import ChatMessage

from chat.haystack_utils.agents import get_agent
from chat.haystack_utils.schemas import ExecutionPlan, ExecutionResult
from chat.haystack_utils.tools import retrieve_documents, reset_retriever_guard
from chat.haystack_utils.tools.quiz import generate_quiz
from chat.haystack_utils.tools.quiz_eval import evaluate_quiz_answers
from chat.models import Message

from .db import run_db
from .html_utils import strip_sources_block
from .output_parsing import is_quiz_flow, pick_final_text_from_output
from .quiz_utils import filename_candidates, looks_like_not_found_html
from .full_file_extraction import try_extract_full_file_answer


def make_context_injection(context_text: str) -> ChatMessage:
    """
    Build a dedicated message that injects the retrieved context into the chat.
    """
    payload = (
        "CONTEXT (retrieved documents):\n"
        "Use ONLY this context to answer. Do NOT browse the internet.\n\n"
        f"{context_text}\n"
    )

    if hasattr(ChatMessage, "from_system"):
        return ChatMessage.from_system(payload)

    return ChatMessage.from_assistant(payload)


async def execute_quiz_evaluation(
    conversation,
    question_full: str,
    history: List[ChatMessage],
    queue: asyncio.Queue,
) -> ExecutionResult:
    """
    Evaluate quiz answers deterministically, without running the general agent.
    Supports both:
    - new markdown quizzes
    - legacy HTML quizzes already stored in history
    """
    msg_obj = Message(conversation=conversation, user_message=question_full)
    await run_db(msg_obj.save)

    last_quiz_text = ""

    # Find the latest assistant message that looks like a quiz.
    # We support both new markdown quizzes and old HTML quizzes.
    for m in reversed(history):
        role = getattr(m, "_role", None) or getattr(m, "role", None) or getattr(m, "role_", None)
        role_str = str(role).lower() if role is not None else ""

        if "assistant" not in role_str:
            continue

        content = getattr(m, "content", None) or getattr(m, "text", None)
        if not isinstance(content, str) or not content.strip():
            continue

        low = content.lower()
        looks_like_legacy_html_quiz = (
            ("<div class=\"quiz" in low)
            or ("<div class=\"quiz-item" in low)
            or ("<ol" in low and "<li>" in low)
        )
        looks_like_markdown_quiz = all(
            re.search(pattern, content, flags=re.IGNORECASE)
            for pattern in [
                r"\*\*\s*1\.",
                r"\n\s*a\)",
                r"\n\s*b\)",
                r"\n\s*c\)",
                r"\n\s*d\)",
            ]
        )

        if looks_like_legacy_html_quiz or looks_like_markdown_quiz:
            last_quiz_text = content.strip()
            break

    print(
        f"[QUIZ_EVAL] found_last_quiz={bool(last_quiz_text)} "
        f"quiz_len={len(last_quiz_text)}"
    )

    if not last_quiz_text:
        result_text = (
            "| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |\n"
            "|----|---------|---------------------|------------------------|-----|\n"
            "| 1  | (brak poprzedniego quizu do oceny) | - | - | ✗ |\n\n"
            "**Wynik: 0/5**"
        )
    else:
        result = evaluate_quiz_answers(
            user_answers=question_full,
            quiz_questions_text=last_quiz_text,
        )
        result_text = (result.get("quiz_result") or "").strip()

        if not result_text:
            result_text = (
                "| Nr | Pytanie | Poprawna odpowiedź | Odpowiedź użytkownika | ✔/✗ |\n"
                "|----|---------|---------------------|------------------------|-----|\n"
                "| 1  | (błąd oceny quizu) | - | - | ✗ |\n\n"
                "**Wynik: 0/5**"
            )

    await queue.put(result_text)
    await queue.put(None)

    full = result_text.strip()

    msg_obj.bot_reply = full
    await run_db(msg_obj.save)

    try:
        await run_db(conversation.update_last_message_time)
    except AttributeError:
        conversation.updated_at = timezone.now()
        await run_db(conversation.save)

    return ExecutionResult(
        text=full,
        html=False,
        used_fast_path=False,
        used_retrieval=False,
    )


async def execute_fast_path_quiz(
    conversation,
    question_full: str,
    quiz_file_token: str,
    queue: asyncio.Queue,
) -> ExecutionResult:
    """
    Execute the direct quiz generation path without invoking the agent.
    New flow expects quiz generator to return markdown, not HTML.
    """
    msg_obj = Message(conversation=conversation, user_message=question_full)
    await run_db(msg_obj.save)

    quiz_text = ""
    used_name = ""

    for cand in filename_candidates(quiz_file_token):
        try:
            out = generate_quiz(
                text="",
                file_name=cand,
                query="",
                top_k=5,
                mode="haystack_all",
            )
            quiz_try = (out.get("quiz_questions_text") or "").strip()
            if quiz_try:
                quiz_text = quiz_try
                used_name = cand
                if not looks_like_not_found_html(quiz_try):
                    break
        except Exception as e:
            print(f"[QUIZ_FAST_PATH ERROR] file_name='{cand}' err={e}")

    if not quiz_text:
        quiz_text = (
            '**Nie mogę wygenerować quizu.** '
            'Podaj poprawną nazwę pliku albo wklej tekst po **"na podstawie:"**.'
        )

    await queue.put(quiz_text)
    await queue.put(None)

    full = quiz_text.strip()

    msg_obj.bot_reply = full
    await run_db(msg_obj.save)

    try:
        await run_db(conversation.update_last_message_time)
    except AttributeError:
        conversation.updated_at = timezone.now()
        await run_db(conversation.save)

    print(f"[QUIZ_FAST_PATH] token='{quiz_file_token}' used='{used_name}'")

    return ExecutionResult(
        text=full,
        html=False,
        used_fast_path=True,
        used_retrieval=False,
    )


async def execute_plan(
    plan: ExecutionPlan,
    conversation,
    question_full: str,
    history: List[ChatMessage],
    queue: asyncio.Queue,
) -> ExecutionResult:
    """
    Execute the runtime plan selected by the planner.
    """
    if plan.route == "fast_quiz" and plan.quiz_file_token:
        return await execute_fast_path_quiz(
            conversation=conversation,
            question_full=question_full,
            quiz_file_token=plan.quiz_file_token,
            queue=queue,
        )

    if plan.route == "quiz_evaluation":
        return await execute_quiz_evaluation(
            conversation=conversation,
            question_full=question_full,
            history=history,
            queue=queue,
        )

    context_text = ""
    if plan.needs_retrieval and plan.retrieval_query:
        reset_retriever_guard()

        target_file_name = plan.target_file_token or plan.quiz_file_token

        conversation_user_id = None
        if getattr(conversation, "user_id", None) is not None:
            conversation_user_id = str(conversation.user_id)
        elif (
            getattr(conversation, "user", None) is not None
            and getattr(conversation.user, "id", None) is not None
        ):
            conversation_user_id = str(conversation.user.id)

        print(
            "[EXECUTION FILE TARGET]",
            {
                "plan.target_file_token": getattr(plan, "target_file_token", None),
                "plan.quiz_file_token": getattr(plan, "quiz_file_token", None),
                "resolved_file_name": target_file_name,
            },
        )

        retrieved = retrieve_documents(
            query=plan.retrieval_query,
            user_id=conversation_user_id,
            top_k=plan.retrieval_top_k or 5,
            file_name=target_file_name,
            mode=plan.retrieval_mode or "haystack_all",
            doc_query_type=plan.doc_query_type,
            full_file_mode=plan.full_file_mode,
        )
        context_text = retrieved.get("context_text", "") or ""

        print(
            f"[PLAN RETRIEVAL] "
            f"query={plan.retrieval_query!r} "
            f"mode={plan.retrieval_mode!r} "
            f"user_id={conversation_user_id!r} "
            f"file_name={target_file_name!r} "
            f"top_k={plan.retrieval_top_k!r} "
            f"full_file_mode={plan.full_file_mode!r} "
            f"context_len={len(context_text)}"
        )

        deterministic_answer = ""
        if plan.full_file_mode and target_file_name:
            deterministic_answer = try_extract_full_file_answer(
                question=question_full,
                file_name=target_file_name,
                context_text=context_text,
            )

        if deterministic_answer:
            await queue.put(deterministic_answer)
            await queue.put(None)

            msg_obj = Message(conversation=conversation, user_message=question_full)
            await run_db(msg_obj.save)

            msg_obj.bot_reply = deterministic_answer
            await run_db(msg_obj.save)

            try:
                await run_db(conversation.update_last_message_time)
            except AttributeError:
                conversation.updated_at = timezone.now()
                await run_db(conversation.save)

            print(
                "[FULL_FILE_EXTRACTION] returned deterministic answer",
                {
                    "file_name": target_file_name,
                    "text_len": len(deterministic_answer),
                },
            )

            return ExecutionResult(
                text=deterministic_answer,
                html=False,
                used_fast_path=False,
                used_retrieval=True,
            )

    messages = history
    if plan.inject_context and context_text.strip():
        context_msg = make_context_injection(context_text)
        messages = messages + [context_msg]
    messages = messages + [ChatMessage.from_user(question_full)]

    last_full_text = ""
    sources_block_started = False
    loop = asyncio.get_running_loop()

    def streaming_callback(chunk):
        nonlocal last_full_text
        nonlocal sources_block_started

        text = (
            getattr(chunk, "content", None)
            or getattr(chunk, "delta", None)
            or (chunk if isinstance(chunk, str) else "")
        )
        if not text:
            return

        if plan.is_quiz:
            preview = (last_full_text + text).lower()
            if (
                "\n**źródła**" in preview
                or "\nźródła:" in preview
                or "\n**sources**" in preview
                or "\nsources:" in preview
            ):
                sources_block_started = True

            if sources_block_started:
                last_full_text += text
                return

        last_full_text += text

        loop.call_soon_threadsafe(
            queue.put_nowait,
            text.replace("\r\n", "\n").replace("\r", "\n"),
        )

    agent = get_agent(streaming_callback=streaming_callback)

    msg_obj = Message(conversation=conversation, user_message=question_full)
    await run_db(msg_obj.save)

    quiz_mode = False
    try:
        output = await sync_to_async(agent.run, thread_sensitive=True)(
            messages=messages,
            tool_kwargs={},
        )

        if plan.needs_retrieval and not context_text.strip():
            print("[PLAN RETRIEVAL] empty context after retrieval")
        quiz_mode = is_quiz_flow(output)

        if not last_full_text.strip():
            picked = pick_final_text_from_output(output)
            if picked:
                if plan.is_quiz:
                    picked = strip_sources_block(picked)
                await queue.put(picked)
                last_full_text += picked

    finally:
        await queue.put(None)

    full = last_full_text.strip()
    if full:
        if plan.is_quiz or quiz_mode:
            full = strip_sources_block(full)

        msg_obj.bot_reply = full
        await run_db(msg_obj.save)

        try:
            await run_db(conversation.update_last_message_time)
        except AttributeError:
            conversation.updated_at = timezone.now()
            await run_db(conversation.save)

        return ExecutionResult(
            text=full,
            html=False,
            used_fast_path=False,
            used_retrieval=bool(context_text.strip()),
        )

    return ExecutionResult(
        text="",
        html=False,
        used_fast_path=False,
        used_retrieval=bool(context_text.strip()),
    )