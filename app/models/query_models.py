from pydantic import BaseModel
from typing import Literal, Union

class QueryIn(BaseModel):
    query: str

class QueryOut(BaseModel):
    query: str
    tool_used: Literal["weather", "math", "llm"]
    result: Union[str, float, int]
