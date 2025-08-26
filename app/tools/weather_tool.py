from typing import Any
import httpx
import re

from .base import Tool
from app.config import get_settings

CITY_PATTERN = re.compile(r"in ([A-Za-z\s]+?)(?:\?|$)", re.IGNORECASE)

class WeatherTool(Tool):
    name = "weather"
    description = "Fetches current weather for a city using OpenWeatherMap API."

    async def run(self, query: str) -> Any:
        city = self._extract_city(query) or get_settings().weather_default_city
        settings = get_settings()
        if not settings.openweather_api_key:
            # Return stubbed data if key missing
            return f"(stub) It's 24°C and sunny in {city}. Provide OPENWEATHER_API_KEY for live data."
        async with httpx.AsyncClient(timeout=10) as client:
            params = {
                "q": city,
                "appid": settings.openweather_api_key,
                "units": settings.weather_units,
            }
            resp = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
            resp.raise_for_status()
            data = resp.json()
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"]
            return f"It's {temp}°C and {description} in {city}."

    def _extract_city(self, query: str) -> str | None:
        m = CITY_PATTERN.search(query)
        if m:
            return m.group(1).strip()
        return None
