import pytest
from fastapi.testclient import TestClient

from streaming.main import app


client = TestClient(app)


def test_stream_requires_token():
    response = client.get(
        "/chat-stream/",
        params={
            "message": "hello",
            "conversation_id": 1,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing token"


def test_stream_rejects_invalid_token():
    response = client.get(
        "/chat-stream/",
        params={
            "message": "hello",
            "conversation_id": 1,
            "token": "invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"