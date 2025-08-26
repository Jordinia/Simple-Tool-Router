"""Tests for the weather tool."""
import pytest
from app.tools.weather_tool import WeatherTool


@pytest.mark.asyncio
async def test_weather_stub():
    tool = WeatherTool()
    # Should use stub if no API key is set or network fails
    result = await tool.run("Paris")
    assert "Paris" in result
    # Should contain either weather data or fallback message
    assert "°C" in result or "don't have access" in result


@pytest.mark.asyncio
async def test_weather_with_city_name():
    tool = WeatherTool()
    # Test with direct city name (how agent will call it)
    result = await tool.run("Tokyo")
    assert "Tokyo" in result or "don't have access" in result
    
    
@pytest.mark.asyncio 
async def test_weather_empty_city():
    tool = WeatherTool()
    # Should use default city when empty
    result = await tool.run("")
    assert isinstance(result, str)
    # Should contain some city name (default or error message)
    assert len(result) > 0
