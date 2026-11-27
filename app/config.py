import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    APP_NAME: str = "Payment Processing Service"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/payments"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/%2F"
    EXCHANGE_NAME: str = "payments"
    QUEUE_NAME: str = "payments.new"
    DEAD_LETTER_QUEUE: str = "payments.dlq"

    # API Key for authentication
    API_KEY: str = os.getenv("API_KEY", "dev-key-change-in-production")

    # Webhook retry configuration
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    WEBHOOK_RETRY_BASE_DELAY: float = 1.0  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


@lru_cache
def get_settings() -> Settings:
    return Settings()
