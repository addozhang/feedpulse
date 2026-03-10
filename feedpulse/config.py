from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///data/feedpulse.db"
    poll_interval_minutes: int = 10
    log_level: str = "INFO"

    model_config = {"env_prefix": "FEEDPULSE_"}


settings = Settings()
