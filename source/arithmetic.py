"""Bounded arithmetic for the calculator examples; never execute Python code."""

import ast
import math
from typing import cast

Number = int | float
MAX_LENGTH = 256
MAX_NODES = 64
MAX_DEPTH = 16
MAX_MAGNITUDE = 10**100
MAX_EXPONENT = 100


def bounded(value: object) -> Number:
    if type(value) not in (int, float):
        raise ValueError("Only real numbers are supported")
    number = cast(Number, value)
    if abs(number) > MAX_MAGNITUDE or not math.isfinite(number):
        raise ValueError("Calculation exceeds the numeric limit")
    return number


def calculate_expression(expression: str) -> Number:
    """Evaluate +, -, *, /, // and bounded powers with unary signs/parentheses."""
    if not expression or len(expression) > MAX_LENGTH:
        raise ValueError("Expression must contain 1 to 256 characters")
    if any(char not in "0123456789+-*/.() " for char in expression):
        raise ValueError("Invalid characters in expression")
    nesting = 0
    for char in expression:
        if char == "(":
            nesting += 1
            if nesting > MAX_DEPTH:
                raise ValueError("Expression nesting exceeds the limit")
        elif char == ")":
            nesting -= 1
    tree = ast.parse(expression.strip(), mode="eval")
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise ValueError("Expression contains too many operations")
    return _calculate(tree.body, 0)


def _calculate(node: ast.AST, depth: int) -> Number:
    if depth > MAX_DEPTH:
        raise ValueError("Expression nesting exceeds the limit")
    if isinstance(node, ast.Constant):
        return bounded(node.value)
    if isinstance(node, ast.UnaryOp):
        value = _calculate(node.operand, depth + 1)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
    if isinstance(node, ast.BinOp):
        left = _calculate(node.left, depth + 1)
        right = _calculate(node.right, depth + 1)
        if isinstance(node.op, ast.Add):
            return bounded(left + right)
        if isinstance(node.op, ast.Sub):
            return bounded(left - right)
        if isinstance(node.op, ast.Mult):
            return bounded(left * right)
        if isinstance(node.op, ast.Div):
            return bounded(left / right)
        if isinstance(node.op, ast.FloorDiv):
            return bounded(left // right)
        if isinstance(node.op, ast.Pow):
            if abs(right) > MAX_EXPONENT:
                raise ValueError("Exponent exceeds the limit")
            return bounded(left**right)
    raise ValueError("Unsupported arithmetic operation")
