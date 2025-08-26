from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_site_url: str | None = Field(default=None, alias="OPENROUTER_SITE_URL")
    openrouter_title: str | None = Field(default=None, alias="OPENROUTER_TITLE")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    weather_default_city: str = Field(default="San Francisco", alias="WEATHER_DEFAULT_CITY")
    weather_units: str = Field(default="metric", alias="WEATHER_UNITS")  # metric for Celsius, imperial for Fahrenheit

@lru_cache
def get_settings() -> Settings:
    return Settings()
