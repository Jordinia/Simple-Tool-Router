"""Tests for the agentic routing functionality."""
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from app.agent import agentic_select_and_run, _get_agent, TOOLS_MAP


class TestAgenticRouting:
    """Test the agentic routing system."""

    @pytest.mark.asyncio
    async def test_math_routing(self):
        """Test that math queries are routed correctly."""
        result = await agentic_select_and_run("What is 42 * 7?")
        
        assert result["tool_used"] == "math"
        assert result["result"] == "294"
        assert "query" in result
        assert "routed_via_agent" in result

    @pytest.mark.asyncio
    async def test_weather_routing(self):
        """Test that weather queries are routed correctly."""
        result = await agentic_select_and_run("Weather in Jakarta?")
        
        assert result["tool_used"] == "weather"
        assert "Jakarta" in result["result"] or "weather" in result["result"].lower()
        assert "query" in result
        assert "routed_via_agent" in result

    @pytest.mark.asyncio
    async def test_llm_routing(self):
        """Test that general queries are routed to LLM."""
        result = await agentic_select_and_run("What is the capital of France?")
        
        assert result["tool_used"] == "llm"
        assert "query" in result
        assert "routed_via_agent" in result

    @pytest.mark.asyncio
    async def test_fallback_routing_math(self):
        """Test fallback routing for math when agent fails."""
        with patch('app.agent._get_agent', return_value=None):
            result = await agentic_select_and_run("What is 10 + 5?")
            
            assert result["tool_used"] == "math"
            assert result["routed_via_agent"] is False

    @pytest.mark.asyncio
    async def test_fallback_routing_weather(self):
        """Test fallback routing for weather when agent fails."""
        with patch('app.agent._get_agent', return_value=None):
            result = await agentic_select_and_run("What's the weather like?")
            
            assert result["tool_used"] == "weather"
            assert result["routed_via_agent"] is False

    @pytest.mark.asyncio
    async def test_fallback_routing_llm(self):
        """Test fallback routing for general queries when agent fails."""
        with patch('app.agent._get_agent', return_value=None):
            result = await agentic_select_and_run("Tell me about history")
            
            assert result["tool_used"] == "llm"
            assert result["routed_via_agent"] is False

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test that agent errors fall back to heuristics."""
        mock_agent = MagicMock()
        mock_agent.ainvoke.side_effect = Exception("Agent failed")
        
        with patch('app.agent._get_agent', return_value=mock_agent):
            result = await agentic_select_and_run("What is 5 + 3?")
            
            # Should fall back to heuristic routing
            assert result["tool_used"] == "math"
            assert result["routed_via_agent"] is False

    @pytest.mark.asyncio
    async def test_structured_output_format(self):
        """Test that the agent returns structured output when working."""
        result = await agentic_select_and_run("What is 2 + 2?")
        
        # Check required fields
        required_fields = ["query", "tool_used", "result", "routed_via_agent"]
        for field in required_fields:
            assert field in result
        
        # Check data types
        assert isinstance(result["query"], str)
        assert isinstance(result["tool_used"], str)
        assert isinstance(result["routed_via_agent"], bool)

    @pytest.mark.asyncio
    async def test_different_math_expressions(self):
        """Test math expressions work correctly."""
        result = await agentic_select_and_run("What is 6 * 7?")
        assert result["tool_used"] == "math"
        assert isinstance(result["result"], str)

    @pytest.mark.asyncio
    async def test_different_weather_queries(self):
        """Test various weather query formats."""
        test_cases = [
            "Weather in Paris",
            "Temperature in Tokyo", 
            "What's the forecast for London?",
            "How's the weather in New York?"
        ]
        
        for query in test_cases:
            result = await agentic_select_and_run(query)
            assert result["tool_used"] == "weather"
            assert isinstance(result["result"], str)

    def test_tools_map_completeness(self):
        """Test that all expected tools are available."""
        expected_tools = ["math", "weather", "llm"]
        
        for tool_name in expected_tools:
            assert tool_name in TOOLS_MAP
            assert hasattr(TOOLS_MAP[tool_name], "run")


class TestAgentCaching:
    """Test agent caching behavior."""
    
    def test_agent_caching(self):
        """Test that agent is cached properly."""
        # First call should build agent
        agent1 = _get_agent()
        
        # Second call should return cached agent
        agent2 = _get_agent()
        
        # Should be the same object (cached)
        assert agent1 is agent2
