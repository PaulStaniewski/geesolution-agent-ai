# chat/haystack_utils/agent_runtime/stream.py

import asyncio
from typing import List

from django.contrib.auth import get_user_model
from haystack.dataclasses import ChatMessage

from chat.haystack_utils.planner import build_execution_plan
from chat.models import Conversation, Message

from .constants import HISTORY_LIMIT
from .db import run_db
from .execution import execute_plan

User = get_user_model()


async def get_streamed_answer_text(
    question: str,
    user_id: int,
    conversation_id: int,
    queue: asyncio.Queue | None = None,
    model: str | None = None,
):
    if queue is None:
        queue = asyncio.Queue()

    try:
        # 1) Conversation ownership check (or create a new one if not found)
        try:
            conversation = await run_db(
                Conversation.objects.get,
                id=conversation_id,
                user_id=user_id,
            )
        except Conversation.DoesNotExist:
            user = await run_db(User.objects.get, id=user_id)
            conversation = await run_db(
                Conversation.objects.create,
                user=user,
                name="Nowa rozmowa",
            )

        # 2) Load history: last N messages, ascending by time
        rows = await run_db(
            lambda: list(
                Message.objects.filter(conversation=conversation)
                .order_by("-created_at")[:HISTORY_LIMIT]
            )
        )
        rows.reverse()

        history: List[ChatMessage] = []
        for m in rows:
            if m.user_message:
                history.append(ChatMessage.from_user(m.user_message))
            if m.bot_reply:
                history.append(ChatMessage.from_assistant(m.bot_reply))

        question_full = (question or "").strip()
        plan = build_execution_plan(question=question_full, history=history)

        print(
            "[EXECUTION_PLAN]",
            f"intent={plan.intent!r}",
            f"route={plan.route!r}",
            f"doc_query_type={plan.doc_query_type!r}",
            f"is_quiz={plan.is_quiz!r}",
            f"is_quiz_answer={plan.is_quiz_answer!r}",
            f"fast_path={plan.use_fast_path_quiz!r}",
            f"needs_retrieval={plan.needs_retrieval!r}",
            f"retrieval_mode={plan.retrieval_mode!r}",
            f"retrieval_top_k={plan.retrieval_top_k!r}",
            f"run_agent={plan.run_agent!r}",
            f"response_mode={plan.response_mode!r}",
        )

        result = await execute_plan(
            plan=plan,
            conversation=conversation,
            question_full=question_full,
            history=history,
            queue=queue,
        )

        print(
            f"[EXECUTION_RESULT] route='{plan.route}' "
            f"fast_path={result.used_fast_path} "
            f"used_retrieval={result.used_retrieval} "
            f"html={result.html} "
            f"text_len={len(result.text)}"
        )

        return result.text

    except Exception as e:
        import traceback

        print(f"[STREAM ERROR] get_streamed_answer_text failed: {e}")
        traceback.print_exc()

        friendly_error = "Wystąpił błąd podczas generowania odpowiedzi. Spróbuj ponownie."

        try:
            await queue.put({
                "type": "error",
                "content": friendly_error,
            })
        except Exception:
            pass

        try:
            await queue.put(None)
        except Exception:
            pass

        return friendly_error