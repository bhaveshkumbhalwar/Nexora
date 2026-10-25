import logging
from typing import List, Dict

from openai import OpenAI, AsyncOpenAI, APIError, APITimeoutError, AuthenticationError, RateLimitError

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


async def stream_chat_completion(messages: List[Dict[str, str]]):
    """Async generator yielding text chunks from the configured provider."""
    client = _build_async_client()
    payload = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=payload,
        max_tokens=settings.llm_max_output_tokens,
        temperature=0.7,
        stream=True,
    )
    try:
        async for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content
            except (AttributeError, IndexError, KeyError):
                delta = None
            if delta:
                yield str(delta)
    finally:
        aclose = getattr(stream, "aclose", None)
        if aclose is not None:
            await aclose()


def chat_completion(messages: List[Dict[str, str]]) -> str:
    """Send conversation messages to the configured provider and return text."""
    client = _build_client()
    payload = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=payload,
            max_tokens=settings.llm_max_output_tokens,
            temperature=0.7,
        )
    except AuthenticationError as exc:
        raise LLMServiceError("Invalid or missing API credentials.") from exc
    except RateLimitError as exc:
        raise LLMServiceError("Rate limit reached. Please try again shortly.") from exc
    except APITimeoutError as exc:
        raise LLMServiceError("The request timed out. Please try again.") from exc
    except APIError as exc:
        raise LLMServiceError(f"Provider error: {exc}") from exc
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
