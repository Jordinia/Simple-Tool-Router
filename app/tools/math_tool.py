import ast
import operator
from typing import Any

from .base import Tool

_ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Num,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Load,
    ast.FloorDiv,
    ast.Constant,
    ast.LShift,
    ast.RShift,
    ast.BitOr,
    ast.BitAnd,
    ast.BitXor,
}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
    ast.BitXor: operator.xor,
}

class MathTool(Tool):
    name = "math"
    description = "Evaluates simple math expressions like '2 + 2 * 5' safely."

    async def run(self, query: str) -> Any:
        expr = self._extract_expression(query)
        if expr is None:
            raise ValueError("No math expression detected")
        tree = ast.parse(expr, mode="eval")
        if not self._is_allowed(tree):
            raise ValueError("Disallowed expression")
        result = self._eval(tree.body)
        return str(result)

    def _extract_expression(self, query: str) -> str | None:
        # Normalize common multiplication notations
        normalized = query.lower().strip()
        
        # Replace common multiplication symbols with *
        normalized = normalized.replace('x', '*')  # 1x2 -> 1*2
        normalized = normalized.replace('×', '*')  # 1×2 -> 1*2
        normalized = normalized.replace('∗', '*')  # math asterisk
        
        # Clean up common phrases
        normalized = normalized.replace("what is", "").replace("calculate", "").replace("?", "").strip()
        
        # Check if it looks like math (has digits and operators)
        if any(ch.isdigit() for ch in normalized) and any(sym in normalized for sym in "+-*/%**"):
            return normalized
        return None

    def _is_allowed(self, node: ast.AST) -> bool:
        for child in ast.walk(node):
            if type(child) not in _ALLOWED_NODES:
                return False
        return True

    def _eval(self, node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num): 
            return node.n
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ValueError("Operator not allowed")
            return _OPERATORS[op_type](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
        raise ValueError("Unsupported expression")
