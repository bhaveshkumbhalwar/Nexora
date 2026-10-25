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


import httpx
from openai import APIStatusError


def _status_error(status_code: int):
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(status_code, request=request)
    return APIStatusError("provider error", response=response, body=None)


def test_sync_retries_503_then_success(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_max_retries", 3)
    monkeypatch.setattr(settings, "llm_retry_base_delay_seconds", 0.0)
    monkeypatch.setattr(settings, "llm_retry_max_delay_seconds", 0.0)

    calls = {"n": 0}

    class FakeMessage:
        content = "ok"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _status_error(503)
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    result = llm_service.chat_completion([{"role": "user", "content": "hi"}])
    assert result == "ok"
    assert calls["n"] == 2


def test_sync_repeated_503_fails(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_max_retries", 3)
    monkeypatch.setattr(settings, "llm_retry_base_delay_seconds", 0.0)
    monkeypatch.setattr(settings, "llm_retry_max_delay_seconds", 0.0)

    calls = {"n": 0}

    class FakeCompletions:
        def create(self, **kwargs):
            calls["n"] += 1
            raise _status_error(503)

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    with pytest.raises(LLMServiceError) as exc:
        llm_service.chat_completion([{"role": "user", "content": "hi"}])
    assert "temporarily busy" in str(exc.value)
    assert calls["n"] == 3


def test_sync_non_retryable_fails_once(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_max_retries", 3)
    monkeypatch.setattr(settings, "llm_retry_base_delay_seconds", 0.0)
    monkeypatch.setattr(settings, "llm_retry_max_delay_seconds", 0.0)

    calls = {"n": 0}

    class FakeCompletions:
        def create(self, **kwargs):
            calls["n"] += 1
            raise _status_error(400)

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "OpenAI", FakeClient)

    with pytest.raises(LLMServiceError):
        llm_service.chat_completion([{"role": "user", "content": "hi"}])
    assert calls["n"] == 1


import pytest


@pytest.mark.asyncio
async def test_stream_retries_503_then_success(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_max_retries", 3)
    monkeypatch.setattr(settings, "llm_retry_base_delay_seconds", 0.0)
    monkeypatch.setattr(settings, "llm_retry_max_delay_seconds", 0.0)

    calls = {"n": 0}

    class FakeDelta:
        content = "hi"

    class FakeChoice:
        delta = FakeDelta()

    class FakeChunk:
        choices = [FakeChoice()]

    class FakeStream:
        def __init__(self, chunks):
            self._chunks = list(chunks)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._chunks:
                raise StopAsyncIteration
            return self._chunks.pop(0)

        async def aclose(self):
            return None

    class FakeCompletions:
        async def create(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _status_error(503)
            return FakeStream([FakeChunk()])

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "AsyncOpenAI", FakeClient)

    collected = []
    async for piece in llm_service.stream_chat_completion([{"role": "user", "content": "hi"}]):
        collected.append(piece)
    assert collected == ["hi"]
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_stream_failure_during_streaming_not_retried(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_model", "gemini-test-model")
    monkeypatch.setattr(settings, "llm_max_retries", 3)
    monkeypatch.setattr(settings, "llm_retry_base_delay_seconds", 0.0)
    monkeypatch.setattr(settings, "llm_retry_max_delay_seconds", 0.0)

    create_calls = {"n": 0}
    yielded = {"n": 0}

    class FakeDelta:
        content = "partial"

    class FakeChoice:
        delta = FakeDelta()

    class FakeChunk:
        choices = [FakeChoice()]

    class FailingStream:
        def __aiter__(self):
            return self

        async def __anext__(self):
            if yielded["n"] == 0:
                yielded["n"] += 1
                return FakeChunk()
            raise _status_error(503)

        async def aclose(self):
            return None

    class FakeCompletions:
        async def create(self, **kwargs):
            create_calls["n"] += 1
            return FailingStream()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm_service, "AsyncOpenAI", FakeClient)

    with pytest.raises(LLMServiceError) as exc:
        async for _ in llm_service.stream_chat_completion([{"role": "user", "content": "hi"}]):
            pass
    assert "temporarily busy" in str(exc.value)
    assert create_calls["n"] == 1


def test_provider_error_code_extraction():
    import httpx
    from openai import APIStatusError

    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(
        503,
        request=request,
        json={"error": {"code": "UNAVAILABLE", "status": "UNAVAILABLE"}},
    )
    exc = APIStatusError("busy", response=response, body=response.json())
    assert llm_service._provider_error_code(exc) == "UNAVAILABLE"
    assert llm_service._provider_error_code(RuntimeError("x")) == "n/a"
