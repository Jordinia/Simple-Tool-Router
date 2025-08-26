from typing import Any
import asyncio
import requests

from .base import Tool
from app.config import get_settings

class WeatherTool(Tool):
    name = "weather"
    description = "Fetches current weather for a city using OpenWeatherMap API."

    async def run(self, city: str) -> Any:
        # city is already extracted by the LLM agent
        if not city or city.strip() == "":
            city = get_settings().weather_default_city
        
        settings = get_settings()

        params = {
            "q": city.strip(),
            "appid": settings.openweather_api_key,
            "units": settings.weather_units,
        }

        try:
            response = await asyncio.to_thread(
                requests.get,
                "https://api.openweathermap.org/data/2.5/weather",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            temp = data.get("main", {}).get("temp", "?")
            description = data.get("weather", [{}])[0].get("description", "unknown conditions")
            country = data.get("sys", {}).get("country", "")
            suffix = f", {country}" if country else ""
            # Prefer API-normalized city name if present
            api_city = data.get("name") or city
            return f"It's {temp}°C and {description} in {api_city}{suffix}."
        except Exception:
            # Fallback for missing API key or network issues
            return f"I don't have access to weather data right now, but you asked about {city}."
