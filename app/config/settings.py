from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"

    bale_bot_token: SecretStr
    bale_api_base_url: AnyUrl = "https://tapi.bale.ai"
    webhook_secret: SecretStr

    openai_api_key: SecretStr
    openai_model: str = "gpt-4o-mini"

    database_url: str = "postgresql+asyncpg://botbale:botbale@localhost:5432/botbale"

    otp_secret: SecretStr
    phone_encryption_key: SecretStr
    otp_ttl_seconds: int = Field(default=300, ge=60, le=1800)
    session_ttl_hours: int = Field(default=24, ge=1, le=24 * 30)

    sms_provider_url: str | None = None
    sms_provider_api_key: SecretStr | None = None
    sms_sender: str = "BotBale"

    free_daily_limit: int = Field(default=5, ge=0, le=100)
    premium_daily_limit: int = Field(default=30, ge=1, le=1000)

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("database_url")
    @classmethod
    def require_async_database_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
