from unittest.mock import patch

import pytest


def test_chat_missing_config(client):
    with patch("app.api.routes.chat.chat_completion", side_effect=__import__("app.services.llm_service", fromlist=["LLMConfigurationError"]).LLMConfigurationError("no key")):
        r = client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 503


def test_chat_valid(client):
    with patch("app.api.routes.chat.chat_completion", return_value="Hi there"):
        r = client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 200
        data = r.json()
        assert data["content"] == "Hi there"
        assert data["conversation_id"] > 0


def test_chat_invalid_empty(client):
    r = client.post("/api/chat", json={"message": "   "})
    # pydantic min_length=1 on raw? message "   " length 3 passes, then route strips -> 422
    assert r.status_code in (422,)


def test_chat_provider_failure(client):
    with patch("app.api.routes.chat.chat_completion", side_effect=__import__("app.services.llm_service", fromlist=["LLMServiceError"]).LLMServiceError("boom")):
        r = client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 502
