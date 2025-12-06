from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Form Validation Agent"

    openrouter_api_key: str = Field("dummy-key", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("openai/gpt-oss-120b:free", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    referer: str = Field("http://localhost", alias="OPENROUTER_REFERER")
    x_title: str = Field("Form Validation Agent", alias="OPENROUTER_X_TITLE")

    database_url: str = Field("postgresql+asyncpg://app:app@db:5432/app", alias="DATABASE_URL")
    base_dir: str = Field(default=".")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


