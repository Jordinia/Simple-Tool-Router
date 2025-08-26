import pytest
import asyncio
from app.tools.math_tool import MathTool

@pytest.mark.asyncio
async def test_math_basic():
    tool = MathTool()
    result = await tool.run("What is 2 + 3 * 4?")
    assert result == "14"

@pytest.mark.asyncio
async def test_math_disallow_eval():
    tool = MathTool()
    with pytest.raises(ValueError):
        await tool.run("__import__('os').system('echo hi')")
