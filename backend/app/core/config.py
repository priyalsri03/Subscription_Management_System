from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Subscription Management System"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./subscription_system.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production-brightloop-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
