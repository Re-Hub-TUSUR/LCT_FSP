from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Runtime configuration. Values come from environment variables or `.env` files.

    The repository keeps a single `.env` at the root (shared with docker compose and Vite);
    `backend/.env` may override it for backend-only experiments.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "KADRY API"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = Field(min_length=1)

    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_issuer: str = "kadry"
    access_token_ttl_minutes: int = Field(default=30, ge=1, le=24 * 60)
    # Survives a closed browser. Logout revokes it; each refresh rotates it.
    refresh_token_ttl_days: int = Field(default=30, ge=1, le=365)

    cors_origins: Annotated[list[str], NoDecode] = []

    # Empty key: development logs the code, production refuses to send.
    # From address must be a verified Resend sender (onboarding@resend.dev works for tests).
    resend_api_key: SecretStr = SecretStr("")
    resend_from: str = "КАДРЫ <onboarding@resend.dev>"

    # Code tasks run on onlinecompiler.io. Empty key: quiz-only tests still work, code tasks
    # answer 503 until the key is set.
    onlinecompiler_api_key: SecretStr = SecretStr("")
    onlinecompiler_url: str = "https://api.onlinecompiler.io"
    # Days before a failed or abandoned test can be retaken / a confirmed grade can be changed.
    assessment_retry_days: int = Field(default=7, ge=0)
    assessment_grade_change_days: int = Field(default=90, ge=0)
    # A grade test passed with at least this score opens the next grade at once.
    assessment_recommend_score: int = Field(default=85, ge=0, le=100)

    # Candidate search. Empty URL: the search runs on the database (tests, CI, low-memory hosts).
    elasticsearch_url: str = ""
    # Alias that points at the current versioned candidates index.
    elasticsearch_index: str = "kadry-candidates"

    # Chat attachments land here; mount a volume in production.
    upload_dir: str = "/data/uploads"
    chat_attachment_limit: int = Field(default=10 * 1024 * 1024, ge=1)

    # Resume recognition through RouterAI (OpenAI-compatible API, https://routerai.ru/models).
    # Empty key: the upload answers 503 and the candidate fills the form by hand.
    routerai_api_key: SecretStr = SecretStr("")
    routerai_url: str = "https://routerai.ru/api/v1"
    resume_parser_model: str = "openai/gpt-6-luna"
    # Sent as `reasoning.effort`; leave empty for a model without reasoning.
    resume_parser_reasoning: str = "low"

    @field_validator("resend_from")
    @classmethod
    def _default_from(cls, value: str) -> str:
        return value.strip() or "КАДРЫ <onboarding@resend.dev>"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard_origin(cls, value: list[str]) -> list[str]:
        # Credentials and `*` cannot be combined: a reflection of any origin would leak the cookie.
        if any(origin == "*" for origin in value):
            msg = "CORS_ORIGINS must list explicit origins; '*' is not allowed"
            raise ValueError(msg)
        return value

    @field_validator("jwt_secret")
    @classmethod
    def _strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_JWT_SECRET_LENGTH:
            msg = f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters"
            raise ValueError(msg)
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
