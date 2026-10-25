from fastapi.middleware.cors import CORSMiddleware

import pytest


def _set_allowed_origins(app, origins):
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            middleware.kwargs["allow_origins"] = list(origins)
    app.middleware_stack = None


def test_preflight_allowed_origin(client):
    from app.main import app

    _set_allowed_origins(app, ["http://localhost:5173", "https://nexora-1-nxe6.onrender.com"])
    response = client.options(
        "/api/chat/stream",
        headers={
            "Origin": "https://nexora-1-nxe6.onrender.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://nexora-1-nxe6.onrender.com"


def test_post_stream_allowed_origin(client):
    async def fake_stream(messages):
        yield "hello"

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("app.api.routes.chat.stream_chat_completion", fake_stream)
        from app.main import app

        _set_allowed_origins(app, ["http://localhost:5173", "https://nexora-1-nxe6.onrender.com"])
        response = client.post(
            "/api/chat/stream",
            headers={"Origin": "https://nexora-1-nxe6.onrender.com", "Content-Type": "application/json"},
            json={"message": "hi"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://nexora-1-nxe6.onrender.com"


def test_preflight_disallowed_origin(client):
    from app.main import app

    _set_allowed_origins(app, ["http://localhost:5173", "https://nexora-1-nxe6.onrender.com"])
    response = client.options(
        "/api/chat/stream",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 400
