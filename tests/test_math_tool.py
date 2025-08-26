import pytest
import asyncio
from app.tools.math_tool import MathTool

@pytest.mark.asyncio
async def test_math_basic():
    tool = MathTool()
    result = await tool.run("What is 2 + 3 * 4?")
    assert result == "14"

@pytest.mark.asyncio
async def test_math_multiplication_variants():
    tool = MathTool()
    # Test different multiplication notations
    assert await tool.run("1x2") == "2"
    assert await tool.run("3x4") == "12"
    assert await tool.run("5×6") == "30"  # Unicode multiplication sign
    assert await tool.run("2x3x4") == "24"

@pytest.mark.asyncio
async def test_math_disallow_eval():
    tool = MathTool()
    with pytest.raises(ValueError):
        await tool.run("__import__('os').system('echo hi')")
