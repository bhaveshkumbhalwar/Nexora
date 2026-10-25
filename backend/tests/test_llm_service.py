import types

import pytest

from app.core.config import settings
from app.services import llm_service
from app.services.llm_service import LLMConfigurationError, LLMServiceError


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", None)
    with pytest.raises(LLMConfigurationError):
        llm_service.chat_completion([{"role": "user", "content": "hi"}])


def test_chat_completion_passes_configured_model(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_base_url", "https://example.com/v1/")
    monkeypatch.setattr(settings, "llm_max_output_tokens", 123)

    captured = {}

    class FakeMessage:
        content = "model answer"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.init_kwargs = kwargs
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    result = llm_service.chat_completion([{"role": "user", "content": "hi"}])

    assert result == "model answer"
    assert captured["model"] == "gemini-test-model"
    assert captured["max_tokens"] == 123
    assert captured["messages"][0]["role"] == "system"
    assert captured["messages"][1] == {"role": "user", "content": "hi"}


def test_provider_failure_raises_service_error(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")

    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    with pytest.raises(LLMServiceError):
        llm_service.chat_completion([{"role": "user", "content": "hi"}])


def test_empty_response_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")

    class FakeMessage:
        content = "   "

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    with pytest.raises(LLMServiceError):
        llm_service.chat_completion([{"role": "user", "content": "hi"}])
