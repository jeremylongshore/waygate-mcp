"""Bound calculator resource use while preserving ordinary arithmetic."""

import importlib.util
from pathlib import Path
from typing import cast

import pytest

from source.example_tools import ExampleTools


@pytest.fixture(params=["current", "retained"])
def calculator(request: pytest.FixtureRequest) -> ExampleTools:
    if request.param == "current":
        return ExampleTools.__new__(ExampleTools)
    path = Path(__file__).resolve().parents[2] / "source-backup-092925/example_tools.py"
    spec = importlib.util.spec_from_file_location("retained_examples", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(ExampleTools, module.ExampleTools.__new__(module.ExampleTools))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", 14),
        ("(25 - 5) / 4", 5),
        ("-3 + +2", -1),
        ("7 // 2", 3),
        ("2**10", 1024),
        ("2**-2", 0.25),
        (".5 * 8", 4),
    ],
)
async def test_supported_arithmetic(
    calculator: ExampleTools, expression: str, expected: int | float
) -> None:
    result = await calculator.calculate(expression)
    assert result["success"] is True
    assert result["result"] == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expression",
    [
        "10**101",
        "9**1000",
        "1" + " " * 256,
        "(" * 20 + "1" + ")" * 20,
        "1+" * 40 + "1",
        "9" * 200 + ".0",
        "(-1)**.5",
        "2**(2**10)",
        "1/0",
        "open('/tmp/fixture')",
        "[1][0]",
        "True",
        "1%2",
        "",
        "1e2",
    ],
)
async def test_unsupported_or_unbounded_input_refused(
    calculator: ExampleTools, expression: str
) -> None:
    result = await calculator.calculate(expression)
    assert result["success"] is False
    assert "result" not in result
