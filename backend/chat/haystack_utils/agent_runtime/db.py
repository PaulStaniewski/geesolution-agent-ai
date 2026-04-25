# chat/haystack_utils/agent_runtime/db.py

from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.db.utils import OperationalError


async def run_db(fn, *args, **kwargs):
    await sync_to_async(close_old_connections, thread_sensitive=True)()

    try:
        return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)
    except OperationalError as e:
        msg = str(e).lower()

        retryable = (
            "connection is closed" in msg
            or "server closed the connection" in msg
            or "terminating connection" in msg
            or "could not connect to server" in msg
        )

        if retryable:
            await sync_to_async(close_old_connections, thread_sensitive=True)()
            return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)

        raise