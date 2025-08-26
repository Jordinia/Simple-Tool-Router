import pytest
import asyncio
from app.tools.weather_tool import WeatherTool

@pytest.mark.asyncio
async def test_weather_stub():
    tool = WeatherTool()
    # Should use stub if no API key is set
    result = await tool.run("What's the weather in Paris?")
    assert "Paris" in result
    assert "stub" in result or "°C" in result

@pytest.mark.asyncio
async def test_weather_city_extraction():
    tool = WeatherTool()
    # Should extract city from query
    assert tool._extract_city("What's the weather in Tokyo?") == "Tokyo"
    assert tool._extract_city("weather in New York?") == "New York"
    assert tool._extract_city("Tell me the weather in London") == "London"
    assert tool._extract_city("weather?") is None
