import os
from pathlib import Path
from typing import Optional, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load .env from the backend directory, regardless of the current
# working directory used to start uvicorn.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "sqlite:///./app.db"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    llm_provider: str = "openai"
    llm_model: str = "gemini-3.1-flash-lite"
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_timeout_seconds: int = 60
    llm_max_output_tokens: int = 512
    llm_context_message_limit: int = 10
    llm_max_retries: int = 2
    llm_retry_base_delay_seconds: float = 0.5
    llm_retry_max_delay_seconds: float = 4.0

    @field_validator("llm_model")
    @classmethod
    def _clean_model(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("LLM_MODEL must not be empty.")
        return value

    @field_validator("llm_base_url")
    @classmethod
    def _clean_base_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        # OpenAI-compatible clients resolve relative paths against this URL.
        # A trailing slash prevents the final path segment from being dropped.
        if not value.endswith("/"):
            value += "/"
        return value

    @property
    def cors_origin_list(self) -> List[str]:
        origins = []
        for origin in self.cors_origins.split(","):
            origin = origin.strip().rstrip("/")
            if origin and origin not in origins:
                origins.append(origin)
        return origins

    @property
    def is_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_api_key.strip())


settings = Settings()
