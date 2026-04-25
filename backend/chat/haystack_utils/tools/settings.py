import os
from openai import OpenAI

# --- Retrieval settings ---
RETRIEVE_TOP_K = int(os.getenv("RETRIEVE_TOP_K", "5"))
MAX_CONTENT = int(os.getenv("MAX_CONTENT", "800"))
DEFAULT_RETRIEVE_MODE = os.getenv("DEFAULT_RETRIEVE_MODE", "haystack_docs")

# --- OpenAI (quiz) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CHAT_MODEL_QUIZ = os.getenv("OPENAI_CHAT_MODEL_QUIZ", "gpt-4o")
OPENAI_CHAT_MODEL_EVAL = os.getenv("OPENAI_CHAT_MODEL_EVAL", "gpt-4o")
OPENAI_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "45"))
QUIZ_TEMP = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

client = OpenAI(api_key=OPENAI_API_KEY)