from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from .tools.math_tool import MathTool
from .tools.weather_tool import WeatherTool
from .tools.llm_tool import LLMTool

router = APIRouter()

TOOLS = [MathTool(), WeatherTool(), LLMTool()]

class QueryIn(BaseModel):
    query: str

class QueryOut(BaseModel):
    query: str
    tool_used: str
    result: str

@router.post("/query", response_model=QueryOut)
async def query_endpoint(payload: QueryIn):
    query = payload.query.strip()
    tool = select_tool(query)
    if not tool:
        raise HTTPException(status_code=400, detail="Could not determine tool for query")
    try:
        result = await tool.run(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return QueryOut(query=query, tool_used=tool.name, result=str(result))

KEYWORDS = {
    "weather": ["weather", "temperature", "rain", "forecast"],
    "math": ["+", "-", "*", "/", "plus", "times"],
}

NAME_TO_TOOL: Dict[str, Any] = {t.name: t for t in TOOLS}

def select_tool(query: str):
    q = query.lower()
    # explicit question patterns
    if any(k in q for k in KEYWORDS["weather"]):
        return NAME_TO_TOOL["weather"]
    # math detection heuristic
    if any(sym in q for sym in ["+", "-", "*", "/"]) and any(ch.isdigit() for ch in q):
        return NAME_TO_TOOL["math"]
    # fallback llm
    return NAME_TO_TOOL["llm"]
