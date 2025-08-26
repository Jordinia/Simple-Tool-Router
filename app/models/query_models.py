
# Pydantic models for /query endpoint request and response schema
from pydantic import BaseModel
from typing import Literal, Union


class QueryIn(BaseModel):
    """
    Pydantic Request model for /query endpoint.
    """
    query: str


class QueryOut(BaseModel):
    """
    Pydantic Response model for /query endpoint.
    """
    query: str
    tool_used: Literal["weather", "math", "llm"]
    result: Union[str, float, int]
