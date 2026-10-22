from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://expense:expense@db:5432/expenses"
    telegram_bot_token: str = ""
    allowed_telegram_user_ids: str = ""
    app_timezone: str = "Asia/Kolkata"
    default_currency: str = "INR"
    cors_origins: str = "http://localhost:3001,http://localhost:5173"
    default_skill: str = "expense_tracking"

    # Preferred provider, tried first. auto uses the free-first fallback order.
    # gemini | groq | openrouter | openai | auto
    default_llm_provider: str = "gemini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_http_referer: str = "http://localhost:3001"
    openrouter_app_name: str = "Sanya"

    # Paid fallback. Used when the free providers above have no key or their call fails.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def allowed_user_ids(self) -> set[str]:
        return {item.strip().lstrip("@") for item in self.allowed_telegram_user_ids.split(",") if item.strip()}


settings = Settings()
