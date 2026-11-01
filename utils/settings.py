from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = "sqlite+aiosqlite:///./notifications.db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost/"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
