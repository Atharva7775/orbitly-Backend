from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from the environment (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development", alias="ORBITLY_ENV")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    session_ttl_minutes: int = Field(default=720, alias="SESSION_TTL_MINUTES")
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    payments_api_url: str = Field(default="https://sandbox.paystream-gateway.example", alias="PAYMENTS_API_URL")
    payments_api_key: str = Field(default="", alias="PAYMENTS_API_KEY")
    payments_timeout_seconds: float = 10.0

    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    mail_from: str = Field(default="Orbitly <hello@orbitly.example>", alias="MAIL_FROM")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
