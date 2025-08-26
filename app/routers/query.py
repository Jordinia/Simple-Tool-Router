from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
from typing import Dict, Any

from app.models.query_models import QueryIn, QueryOut
from app.agent import agentic_select_and_run, agentic_stream

router = APIRouter()

def select_tool(query: str):  # simple fallback for other modules (e.g. ws)
    q = query.lower()
    if any(k in q for k in ["weather", "temperature", "rain", "forecast"]):
        return "weather"
    if any(sym in q for sym in ["+", "-", "*", "/"]) and any(ch.isdigit() for ch in q):
        return "math"
    return "llm"

@router.post("/query", response_model=QueryOut)
async def query_endpoint(payload: QueryIn):
    query = payload.query.strip()
    try:
        # We still compute a dict for the response_model (docs/schema) while streaming.
        # FastAPI will not build body since we override with StreamingResponse.
        stream = agentic_stream(query)
        return StreamingResponse(stream, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
