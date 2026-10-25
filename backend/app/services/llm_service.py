import asyncio
import logging
import random
from typing import List, Dict, Optional

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when the LLM provider is not configured."""


class LLMServiceError(Exception):
    """Raised when the LLM request fails."""


SYSTEM_PROMPT = (
    "You are a helpful, accurate, and concise assistant. "
    "Answer questions across many topics. Use Markdown for structure: headings, lists, "
    "tables, and fenced code blocks. Explain complex ideas simply when asked. "
    "Be honest about uncertainty. Do not fabricate facts."
)

_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code in _RETRYABLE_STATUS_CODES or exc.status_code >= 500
    return False


def _status_code(exc: Exception) -> str:
    if isinstance(exc, APIStatusError):
        return str(exc.status_code)
    if isinstance(exc, APITimeoutError):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection"
    return "unknown"


def _retry_after(exc: Exception) -> Optional[float]:
    if not isinstance(exc, APIStatusError):
        return None
    response = getattr(exc, "response", None)
    if response is None:
        return None
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("Retry-After") or headers.get("retry-after")
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _retry_delay(attempt: int, exc: Exception) -> float:
    retry_after = _retry_after(exc)
    if retry_after is not None:
        return min(max(retry_after, 0.0), settings.llm_retry_max_delay_seconds)
    base = min(
        settings.llm_retry_max_delay_seconds,
        settings.llm_retry_base_delay_seconds * (2 ** (attempt - 1)),
    )
    jitter = random.uniform(0.0, min(1.0, base * 0.25 + 0.1))
    return min(settings.llm_retry_max_delay_seconds, base + jitter)


def _map_provider_error(exc: Exception) -> Exception:
    if isinstance(exc, LLMConfigurationError):
        return exc
    if isinstance(exc, AuthenticationError):
        return LLMServiceError("Invalid or missing API credentials.")
    if isinstance(exc, BadRequestError):
        return LLMServiceError("The request was rejected by the model provider.")
    if isinstance(exc, RateLimitError):
        return LLMServiceError("Rate limit reached. Please try again shortly.")
    if isinstance(exc, APITimeoutError):
        return LLMServiceError("The request timed out. Please try again.")
    if isinstance(exc, APIStatusError):
        if exc.status_code in {503, 502, 504}:
            return LLMServiceError("The AI model is temporarily busy. Please try again in a moment.")
        if exc.status_code == 429:
            return LLMServiceError("Rate limit reached. Please try again shortly.")
        return LLMServiceError(f"Provider error: {exc}")
    if isinstance(exc, APIError):
        return LLMServiceError(f"Provider error: {exc}")
    return LLMServiceError("Unexpected error while contacting the model.")


def _build_client() -> OpenAI:
    api_key = (settings.llm_api_key or "").strip()
    if not api_key:
        raise LLMConfigurationError(
            "LLM API key is not configured. Set LLM_API_KEY in backend/.env."
        )
    kwargs = {"api_key": api_key, "timeout": settings.llm_timeout_seconds}
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return OpenAI(**kwargs)


def _build_async_client() -> AsyncOpenAI:
    api_key = (settings.llm_api_key or "").strip()
    if not api_key:
        raise LLMConfigurationError(
            "LLM API key is not configured. Set LLM_API_KEY in backend/.env."
        )
    kwargs = {"api_key": api_key, "timeout": settings.llm_timeout_seconds}
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return AsyncOpenAI(**kwargs)


async def _create_async_stream(client, payload):
    last_exc = None
    max_attempts = max(1, settings.llm_max_retries)
    for attempt in range(1, max_attempts + 1):
        try:
            return await client.chat.completions.create(
                model=settings.llm_model,
                messages=payload,
                max_tokens=settings.llm_max_output_tokens,
                temperature=0.7,
                stream=True,
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_retryable(exc) or attempt == max_attempts:
                raise _map_provider_error(exc) from exc
            delay = _retry_delay(attempt, exc)
            logger.warning(
                "Transient provider error status=%s attempt=%d/%d; retrying in %.2fs",
                _status_code(exc),
                attempt,
                max_attempts,
                delay,
            )
            await asyncio.sleep(delay)
    raise _map_provider_error(last_exc) from last_exc


def _create_sync_completion(client, payload):
    last_exc = None
    max_attempts = max(1, settings.llm_max_retries)
    for attempt in range(1, max_attempts + 1):
        try:
            return client.chat.completions.create(
                model=settings.llm_model,
                messages=payload,
                max_tokens=settings.llm_max_output_tokens,
                temperature=0.7,
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_retryable(exc) or attempt == max_attempts:
                raise _map_provider_error(exc) from exc
            delay = _retry_delay(attempt, exc)
            logger.warning(
                "Transient provider error status=%s attempt=%d/%d; retrying in %.2fs",
                _status_code(exc),
                attempt,
                max_attempts,
                delay,
            )
            import time
            time.sleep(delay)
    raise _map_provider_error(last_exc) from last_exc


async def stream_chat_completion(messages: List[Dict[str, str]]):
    """Async generator yielding text chunks from the configured provider."""
    client = _build_async_client()
    payload = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    stream = await _create_async_stream(client, payload)
    try:
        async for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content
            except (AttributeError, IndexError, KeyError):
                delta = None
            if delta:
                yield str(delta)
    except Exception as exc:  # noqa: BLE001
        raise _map_provider_error(exc) from exc
    finally:
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            await aclose()


def chat_completion(messages: List[Dict[str, str]]) -> str:
    """Send conversation messages to the configured provider and return text."""
    client = _build_client()
    payload = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    try:
        response = _create_sync_completion(client, payload)
    except (LLMConfigurationError, LLMServiceError):
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected LLM failure")
        raise LLMServiceError("Unexpected error while contacting the model.") from exc

    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError) as exc:
        raise LLMServiceError("Malformed response from provider.") from exc

    if not content or not str(content).strip():
        raise LLMServiceError("The model returned an empty response.")
    return str(content).strip()
