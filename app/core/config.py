from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Knowledge Assistant"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

'''

What this does:

BaseSettings reads configuration from environment variables and .env.
Type annotations validate the configuration.
get_settings() provides one cached settings object instead of recreating it repeatedly.
extra="ignore" prevents unexpected .env entries from crashing the application.

'''