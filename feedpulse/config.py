from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    db_path: str = "data/feedpulse.db"
    poll_interval_minutes: int = 10
    log_level: str = "INFO"
    max_concurrent_feeds: int = 10
    initial_fetch_limit: int = 5
    language: str = "en"
    api_enabled: bool = True
    api_port: int = 8000

    model_config = {"env_prefix": "FEEDPULSE_"}


settings = Settings()
