import os

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.utils import Secret

from .prompts import GPT_PROMPT
from .tools import document_tool_for, quiz_tool, evaluate_quiz_tool

# ---------------------------------------------------------------------
# HARD-CODED MODEL
# This agent is locked to a single model to keep runtime and behavior
# deterministic across environments. If you later want to change it,
# edit the string below (no environment variable override).
# ---------------------------------------------------------------------
MODEL_NAME = "gpt-4.1"


# Extra instructions specifically about URLs in retrieved documents
URL_INSTRUCTIONS = """
You are NOT browsing the live internet. However, the documents you see may already
contain canonical URLs in their metadata or inline text (for example: "URL: https://docs.haystack.deepset.ai/...").

If the user asks for:
- a link to the documentation,
- a link to the page you used,
- "dokładnie tę dokumentację" or similar,

then:

1. Look for any URLs in the context you were given (for example, lines containing "URL: ...").
2. If such a URL exists, reuse it exactly and return it to the user.
3. Do NOT say that you cannot provide a link if the context already contains a URL.
4. Do NOT invent or guess new URLs that are not present in the context.
"""


def get_agent(
    streaming_callback=None,
) -> Agent:
    """
    Construct and return a minimal Agent configured for document QA + quizzes.

    Key design decisions:
    - Single fixed model (MODEL_NAME) to avoid branching logic at runtime.
    - Only the haystack retriever is exposed as a tool, plus quiz tools.
    - Streaming callback can be provided to stream generation tokens back
      to the caller (used by FastAPI SSE / frontend streaming).
    - State schema keeps only the fields we actually use for RAG + quizzes.
    """

    # ---------------------------
    # Generator / model settings
    # ---------------------------
    # These are intentionally conservative defaults (safe for production).
    max_tokens = int(os.getenv("GPT_MAX_TOKENS", "1500"))       # max response tokens
    temperature = float(os.getenv("GPT_TEMPERATURE", "0.2"))  # low temperature = deterministic
    max_steps = int(os.getenv("AGENT_STEPS", "6"))            # max reasoning/tool steps

    # SECURITY: API key retrieval is done via haystack.utils.Secret which
    # wraps environment access. Keep the key only in env and never hardcode.
    chat_gen = OpenAIChatGenerator(
        api_key=Secret.from_env_var("OPENAI_API_KEY"),
        model=MODEL_NAME,
        streaming_callback=streaming_callback,
        generation_kwargs={
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )

    # ---------------------------
    # Tools
    # ---------------------------
    # - document_tool_for(mode="haystack"): retrieves documents from the
    #   central haystack document store (the only retriever we keep).
    # - quiz_tool / evaluate_quiz_tool: domain-specific tools to produce
    #   quizzes and evaluate answers. They remain part of the agent's toolset.
    tools = [
        document_tool_for(mode="haystack_all", name="document_retriever"),
        quiz_tool,
        evaluate_quiz_tool,
    ]

    # ---------------------------
    # Agent construction
    # ---------------------------
    # - system_prompt: the global system prompt controlling base behavior.
    # - exit_conditions: what the agent considers an answer-complete signal.
    # - max_agent_steps: protects against runaway tool loops.
    # - raise_on_tool_invocation_failure=False: tolerate transient tool errors
    #   so the agent can still attempt to continue gracefully.
    # - state_schema: typed container for the agent's ephemeral state between steps.
    combined_prompt = f"{GPT_PROMPT}\n\n{URL_INSTRUCTIONS}"

    return Agent(
        chat_generator=chat_gen,
        tools=tools,
        system_prompt=combined_prompt,
        exit_conditions=["text", "quiz_generator", "quiz_evaluator"],
        max_agent_steps=max_steps,
        raise_on_tool_invocation_failure=False,
        state_schema={
            "retrieved_docs": {"type": list},
            "quiz_questions_text": {"type": str},
            "quiz_result": {"type": str},
        },
    )
