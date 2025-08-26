"""Agentic routing using LangChain ReAct to choose tools.

Design:
- One lightweight LLM (Gemini) decides which tool to call.
- Weather / Math: only routing LLM call + direct underlying tool run (total 1 LLM call).
- General queries: routing decides "llm" then we call our existing LLM tool (2 LLM calls total: routing + answer).

Requires GOOGLE_API_KEY for ChatGoogleGenerativeAI.
Falls back to legacy heuristic if LangChain or API key unavailable.
"""
from __future__ import annotations

from typing import Callable, Any, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.tools.math_tool import MathTool
from app.tools.weather_tool import WeatherTool
from app.tools.llm_tool import LLMTool

math_tool = MathTool()
weather_tool = WeatherTool()
llm_tool = LLMTool()

TOOLS_MAP = {
    "math": math_tool,
    "weather": weather_tool,
    "llm": llm_tool,
}

# Pydantic model for structured output
class ToolSelection(BaseModel):
    tool: str = Field(description="Selected tool name: math, weather, or llm")
    input: str = Field(description="Input string to pass to the selected tool")

# Tool descriptions for the prompt
TOOL_DESCRIPTIONS = """
- math: Evaluate arithmetic expressions. Input should be raw expression like "42 * 7", "10 + 5 / 2", "2**8"
- weather: Get weather for a location. Input should be ONLY the city name like "Paris", "New York", "Jakarta", "Tokyo"
- llm: General knowledge questions. Input should be the original user question
"""

def build_prompt_template() -> Any:
    """Build prompt template with Pydantic output parser."""
    if not PromptTemplate or not PydanticOutputParser:
        return None
    
    parser = PydanticOutputParser(pydantic_object=ToolSelection)
    
    prompt = PromptTemplate(
        template="""You are a tool router that selects the best tool for user questions.

Available tools:
{tools}

Instructions:
- Analyze the user question carefully
- Select the most appropriate tool from: math, weather, llm
- For math queries: extract ONLY the mathematical expression (e.g., "42 * 7")
- For weather queries: extract ONLY the city name (e.g., "Jakarta", "New York", "Paris") - NO extra words
- For other queries: use the original question as input

IMPORTANT: For weather, output ONLY the city name, nothing else!

{format_instructions}

User question: {input}""",
        input_variables=["tools", "input"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    return prompt, parser

_agent_chain: Any = None  # store built LangChain chain


def _build_agent() -> Any:  # pragma: no cover - network path
    settings = get_settings()
    if not settings.google_api_key or not PromptTemplate:
        return None
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.google_api_key, temperature=0)
    
    prompt_and_parser = build_prompt_template()
    if not prompt_and_parser:
        return None
    
    prompt, parser = prompt_and_parser
    
    # Create LangChain LCEL chain: prompt | llm | parser
    chain = prompt | llm | parser
    return chain


def _get_agent() -> Any:
    global _agent_chain
    if _agent_chain is None:
        _agent_chain = _build_agent()
    return _agent_chain


async def agentic_select_and_run(query: str) -> dict[str, Any]:
    """Route query via agent; run actual tool; return structured dict.

    Returns: {query, tool_used, result, routed_via_agent: bool, raw_decision?: str}
    """
    agent_chain = _get_agent()
    routed_via_agent = False
    tool_name: str | None = None
    tool_input = query
    raw_decision = None

    if agent_chain:
        try:  # pragma: no cover network path
            # Invoke the LangChain chain with structured output
            result = await agent_chain.ainvoke({
                "tools": TOOL_DESCRIPTIONS,
                "input": query
            })
            
            # result is now a ToolSelection Pydantic model
            tool_name = result.tool
            tool_input = result.input
            routed_via_agent = True
            raw_decision = f"Selected: {tool_name}, Input: {tool_input}"
            
        except Exception as e:
            tool_name = None
            raw_decision = f"Agent failed: {str(e)}"

    # Fallback: simple heuristics if agent missing/fails
    if tool_name not in TOOLS_MAP:
        q = query.lower()
        if any(k in q for k in ["weather", "temperature", "rain", "forecast"]):
            tool_name = "weather"
        elif any(sym in q for sym in ["+", "-", "*", "/"]) and any(ch.isdigit() for ch in q):
            tool_name = "math"
        else:
            tool_name = "llm"

    # Execute chosen tool
    tool = TOOLS_MAP[tool_name]
    result = await tool.run(tool_input)

    return {
        "query": query,
        "tool_used": tool_name,
        "result": result,
        "routed_via_agent": routed_via_agent,
        **({"raw_decision": raw_decision} if raw_decision and routed_via_agent else {}),
    }


async def agentic_stream(query: str):
    """Async generator yielding a single JSON line for streaming response.

    Keeps streaming concerns out of the router so the function can be reused.
    """
    payload = await agentic_select_and_run(query)
    import json as _json
    yield _json.dumps({
        "query": payload["query"],
        "tool_used": payload["tool_used"],
        "result": payload["result"],
    }) + "\n"
