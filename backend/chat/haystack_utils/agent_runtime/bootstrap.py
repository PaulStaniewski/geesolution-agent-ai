# chat/haystack_utils/agent_runtime/bootstrap.py

import os
from dotenv import load_dotenv

# Load environment variables early (before Django setup)
load_dotenv()

# Standalone Django setup (FastAPI worker process)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_ai.settings")

import django  # noqa: E402
django.setup()