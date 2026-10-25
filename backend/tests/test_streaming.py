import json

import pytest


async def _fake_stream(messages, captured):
    captured["messages"] = messages
    for piece in ["Hello", " world"]:
        yield piece


def _parse_sse(text):
    events = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))
    return events


def test_stream_success(client):
    captured = {}

    async def fake_stream(messages):
        async for piece in _fake_stream(messages, captured):
            yield piece

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.routes.chat.stream_chat_completion", fake_stream)
        with client.stream("POST", "/api/chat/stream", json={"message": "hi there"}) as r:
            assert r.status_code == 200
            body = r.read().decode()

    events = _parse_sse(body)
    types = [e["type"] for e in events]
    assert "meta" in types
    assert types.count("chunk") == 2
    assert "done" in types
    assert "".join(e["content"] for e in events if e["type"] == "chunk") == "Hello world"

    # Conversation persisted with assistant content.
    conv_id = next(e["conversation_id"] for e in events if e["type"] == "meta")
    detail = client.get(f"/api/conversations/{conv_id}").json()
    assert detail["messages"][-1]["role"] == "assistant"
    assert detail["messages"][-1]["content"] == "Hello world"

    # Context was passed to the model.
    assert any(m["role"] == "user" and m["content"] == "hi there" for m in captured["messages"])


def test_stream_error(client):
    async def failing_stream(messages):
        raise __import__("app.services.llm_service", fromlist=["LLMServiceError"]).LLMServiceError("boom")
        yield  # pragma: no cover

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.routes.chat.stream_chat_completion", failing_stream)
        with client.stream("POST", "/api/chat/stream", json={"message": "hi"}) as r:
            assert r.status_code == 200
            body = r.read().decode()

    events = _parse_sse(body)
    assert any(e["type"] == "error" and "boom" in e["detail"] for e in events)


def test_stream_empty(client):
    async def empty_stream(messages):
        return
        yield  # pragma: no cover

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.routes.chat.stream_chat_completion", empty_stream)
        with client.stream("POST", "/api/chat/stream", json={"message": "hi"}) as r:
            assert r.status_code == 200
            body = r.read().decode()

    events = _parse_sse(body)
    assert any(e["type"] == "error" and "empty" in e["detail"].lower() for e in events)
