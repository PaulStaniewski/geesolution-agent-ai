# streaming/main.py
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

# === JWT config ===
JWT_ALG = os.getenv("SIMPLE_JWT_ALGORITHM", "HS256")
JWT_ISS = os.getenv("SIMPLE_JWT_ISSUER", "geebot-api")
JWT_AUD = os.getenv("SIMPLE_JWT_AUDIENCE", "geebot-web")

# Klucz weryfikacji:
# - dla HS*: SIMPLE_JWT_SIGNING_KEY, albo SECRET_KEY (domyślny w SimpleJWT), ewentualnie JWT_SECRET jako fallback
# - dla RS*: publiczny klucz z pliku wskazanego w JWT_PUBLIC_KEY_FILE
if JWT_ALG.startswith("HS"):
    JWT_VERIFY_KEY = (
        os.getenv("SIMPLE_JWT_SIGNING_KEY")
        or os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET")
    )
    if not JWT_VERIFY_KEY:
        raise RuntimeError(
            "JWT verify key missing. Ustaw SIMPLE_JWT_SIGNING_KEY lub SECRET_KEY (ew. JWT_SECRET) "
            "i upewnij się, że zgadza się z kluczem używanym przez Django SimpleJWT."
        )
else:
    pub_path = os.getenv("JWT_PUBLIC_KEY_FILE")
    if not pub_path or not os.path.exists(pub_path):
        raise RuntimeError("JWT_PUBLIC_KEY_FILE is missing or invalid")
    with open(pub_path, "r") as f:
        JWT_VERIFY_KEY = f.read()

# === CORS ===
origins = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if o.strip()
]

app = FastAPI(
    title="GeeBOT Streaming API",
    description="API documentation for GeeBOT's streaming chat powered by Haystack.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,  # używamy Bearer/query, więc cookies nie są potrzebne
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Rate limiting (SlowAPI) ===
limiter = Limiter(key_func=get_remote_address, headers_enabled=True)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# === Inne ustawienia
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "4000"))


def auth_dep(
    authorization: str | None = Header(None),
    token: str | None = Query(None),
):
    """
    Prosta autoryzacja: preferujemy nagłówek Authorization: Bearer <JWT>,
    ale wspieramy też legacy ?token=...
    """
    raw = None
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            raw = parts[1]
    raw = raw or token
    if not raw:
        raise HTTPException(status_code=401, detail="Missing token")

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
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/chat-stream/")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,
    message: str,
    conversation_id: int,    
    user_id: int | None = Query(None),  # legacy porównanie; realnie użyjemy usera z JWT
    auth=Depends(auth_dep),
    model: str | None = Query(None),
):
    """
    SSE stream czatu. Wysyła surowe delta-chunki tekstu z mikrobatchingiem.
    Protokół:
      - 'data: <chunk>' linie z zakończeniem \n\n,
      - '\n' w treści zamieniane są na [[NL]],
      - na końcu 'data: [DONE]'.
    """
    jwt_user_id = auth.get("user_id") or auth.get("sub")
    if jwt_user_id is None:
        raise HTTPException(401, detail="JWT missing user_id")

    # opcjonalne sprawdzenie zgodności legacy user_id z query
    if user_id is not None and int(user_id) != int(jwt_user_id):
        raise HTTPException(403, detail="User mismatch")

    effective_user_id = int(jwt_user_id)

    # walidacja wejścia
    if not message or not message.strip():
        raise HTTPException(400, detail="Empty message")
    if len(message) > MAX_PROMPT_CHARS:
        raise HTTPException(413, detail="Message too long")

    # IP do logów
    client_ip = (
        (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )

    async def event_generator():
        # prelude keep-alive
        yield ":\n\n"

        response_text: list[str] = []
        q: asyncio.Queue[str | None] = asyncio.Queue()

        # uruchamiamy generację w tle
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
        FLUSH_MS = float(os.getenv("SSE_FLUSH_MS", "35"))
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
                chunk = await asyncio.wait_for(q.get(), timeout=0.05)
            except asyncio.TimeoutError:
                chunk = ""

            if chunk is None:
                # koniec strumienia — doflushuj
                if buffer:
                    out = "".join(buffer)
                    yield f"data: {out}\n\n"
                    response_text.append(out)
                    buffer.clear()
                break

            if chunk:
                # normalizacja i zamiana nowej linii
                chunk = chunk.replace("\r\n", "\n").replace("\r", "\n")
                chunk = chunk.replace("\n", "[[NL]]")
                buffer.append(chunk)

            now = time.monotonic()
            if should_flush(now):
                out = "".join(buffer)
                buffer.clear()
                last_flush = now
                yield f"data: {out}\n\n"
                response_text.append(out)

        final_text = "".join(response_text).replace("[[NL]]", "\n")
        print(f"[DEBUG] Final streamed text (ip={client_ip}): {final_text}")
        yield "data: [DONE]\n\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "X-Client-IP": client_ip,
    }
    return StreamingResponse(
        event_generator(), media_type="text/event-stream", headers=headers
    )
