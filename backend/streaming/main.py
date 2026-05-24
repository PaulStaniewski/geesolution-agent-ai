from fastapi import FastAPI, Query, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import os.path
import time
import asyncio
import jwt

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from chat.haystack_utils.agent_runtime import get_streamed_answer_text


print("DEBUG: GeeBOT Streaming API loaded")


# === JWT configuration ===

JWT_ALG = os.getenv("SIMPLE_JWT_ALGORITHM", "HS256")
JWT_ISS = os.getenv("SIMPLE_JWT_ISSUER", "geebot-api")
JWT_AUD = os.getenv("SIMPLE_JWT_AUDIENCE", "geebot-web")


# JWT verification key:
# - for HS* algorithms:
#   SIMPLE_JWT_SIGNING_KEY or SECRET_KEY
#   (SimpleJWT default), optionally JWT_SECRET as fallback
#
# - for RS* algorithms:
#   public key loaded from JWT_PUBLIC_KEY_FILE

if JWT_ALG.startswith("HS"):
    JWT_VERIFY_KEY = (
        os.getenv("SIMPLE_JWT_SIGNING_KEY")
        or os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET")
    )

    if not JWT_VERIFY_KEY:
        raise RuntimeError(
            "JWT verification key missing. "
            "Set SIMPLE_JWT_SIGNING_KEY or SECRET_KEY "
            "(optionally JWT_SECRET as fallback) "
            "and ensure it matches the key used by Django SimpleJWT."
        )

else:
    pub_path = os.getenv("JWT_PUBLIC_KEY_FILE")

    if not pub_path or not os.path.exists(pub_path):
        raise RuntimeError("JWT_PUBLIC_KEY_FILE is missing or invalid")

    with open(pub_path, "r") as f:
        JWT_VERIFY_KEY = f.read()


# === CORS configuration ===

origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173",
    ).split(",")
    if o.strip()
]


app = FastAPI(
    title="GeeBOT Streaming API",
    description="Streaming API for GeeBOT chat powered by Haystack.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # Bearer/query auth is used, cookies are not required
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Rate limiting ===

limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(SlowAPIMiddleware)


# === General settings ===

MAX_PROMPT_CHARS = int(
    os.getenv("MAX_PROMPT_CHARS", "4000")
)


def auth_dep(
    authorization: str | None = Header(None),
    token: str | None = Query(None),
):
    """
    Simple JWT authentication.

    Preferred method:
    Authorization: Bearer <JWT>

    Legacy fallback:
    ?token=<JWT> query parameter
    for native EventSource compatibility.
    """

    raw = None

    if authorization:
        parts = authorization.split(" ", 1)

        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw = parts[1]

    raw = raw or token

    if not raw:
        raise HTTPException(
            status_code=401,
            detail="Missing token",
        )

    try:
        payload = jwt.decode(
            raw,
            JWT_VERIFY_KEY,
            algorithms=[JWT_ALG],
            issuer=JWT_ISS,
            audience=JWT_AUD,
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


@app.get("/chat-stream/")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,
    message: str,
    conversation_id: int,
    user_id: int | None = Query(None),  # Legacy validation only
    auth=Depends(auth_dep),
    model: str | None = Query(None),
):
    """
    SSE chat stream endpoint.

    Sends raw text delta chunks using micro-batching.

    Protocol:
    - `data: <chunk>` messages terminated with `\\n\\n`
    - newline characters are encoded as `[[NL]]`
    - stream ends with `data: [DONE]`
    """

    jwt_user_id = auth.get("user_id") or auth.get("sub")

    if jwt_user_id is None:
        raise HTTPException(
            status_code=401,
            detail="JWT missing user_id",
        )

    # Optional legacy consistency validation
    if user_id is not None and int(user_id) != int(jwt_user_id):
        raise HTTPException(
            status_code=403,
            detail="User mismatch",
        )

    effective_user_id = int(jwt_user_id)

    # Input validation
    if not message or not message.strip():
        raise HTTPException(
            status_code=400,
            detail="Empty message",
        )

    if len(message) > MAX_PROMPT_CHARS:
        raise HTTPException(
            status_code=413,
            detail="Message too long",
        )

    # Client IP for debug logs
    client_ip = (
        (request.headers.get("x-forwarded-for") or "")
        .split(",")[0]
        .strip()
        or (request.client.host if request.client else "unknown")
    )

    async def event_generator():
        # SSE keep-alive prelude
        yield ":\n\n"

        response_text: list[str] = []

        q: asyncio.Queue[str | None] = asyncio.Queue()

        # Start background streaming generation
        asyncio.create_task(
            get_streamed_answer_text(
                question=message.strip(),
                user_id=effective_user_id,
                conversation_id=conversation_id,
                queue=q,
                model=model,
            )
        )

        buffer: list[str] = []

        last_flush = time.monotonic()

        FLUSH_MS = float(
            os.getenv("SSE_FLUSH_MS", "35")
        )

        FLUSH_EVERY = FLUSH_MS / 1000.0

        def should_flush(now: float) -> bool:
            if not buffer:
                return False

            tail = buffer[-1]

            return (
                (now - last_flush) >= FLUSH_EVERY
                or tail.endswith("[[NL]]")
            )

        while True:
            try:
                chunk = await asyncio.wait_for(
                    q.get(),
                    timeout=0.05,
                )

            except asyncio.TimeoutError:
                chunk = ""

            if chunk is None:
                # End of stream — flush remaining buffer
                if buffer:
                    out = "".join(buffer)

                    yield f"data: {out}\n\n"

                    response_text.append(out)

                    buffer.clear()

                break

            if chunk:
                # Normalize line endings and encode newlines
                chunk = (
                    chunk
                    .replace("\r\n", "\n")
                    .replace("\r", "\n")
                )

                chunk = chunk.replace("\n", "[[NL]]")

                buffer.append(chunk)

            now = time.monotonic()

            if should_flush(now):
                out = "".join(buffer)

                buffer.clear()

                last_flush = now

                yield f"data: {out}\n\n"

                response_text.append(out)

        final_text = "".join(response_text).replace(
            "[[NL]]",
            "\n",
        )

        print(
            f"[DEBUG] Stream completed "
            f"(ip={client_ip}, chars={len(final_text)})"
        )

        yield "data: [DONE]\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-Client-IP": client_ip,
    }

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )