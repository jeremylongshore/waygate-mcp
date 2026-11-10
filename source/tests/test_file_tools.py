"""File boundaries and command results using disposable local resources."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from source import mcp_tools
from source.exceptions import MCPToolError
from source.mcp_tools import MCPToolsHandler


@pytest.fixture
def handler(tmp_path: Path) -> MCPToolsHandler:
    tool = MCPToolsHandler(str(tmp_path))
    tool.allowed_paths = [tmp_path / "allowed"]
    tool.allowed_paths[0].mkdir()
    return tool


@pytest.mark.asyncio
async def test_file_roundtrip_listing_and_search(handler: MCPToolsHandler) -> None:
    root = handler.allowed_paths[0]
    target = root / "nested" / "Needle.txt"
    result = await handler.write_file({"path": str(target), "content": "A needle café"})
    assert result["size"] == len("A needle café".encode())
    assert (await handler.read_file({"path": str(target)}))[
        "content"
    ] == "A needle café"
    assert (await handler.list_directory({"path": str(root)}))["entries"][0][
        "type"
    ] == "directory"
    listing = await handler.list_directory(
        {"path": str(root), "recursive": True, "pattern": "*.txt"}
    )
    assert listing["count"] == 1
    assert listing["entries"][0]["path"] == str(target)
    for mode, matches in [
        ("filename", ["filename"]),
        ("content", ["content"]),
        ("both", ["filename", "content"]),
    ]:
        found = await handler.search_files(
            {"path": str(root), "query": "NEEDLE", "type": mode}
        )
        assert found["count"] == 1
        assert found["results"][0]["match_type"] == matches
    assert (await handler.search_files({"path": str(root), "query": "absent"}))[
        "count"
    ] == 0
    await handler.write_file({"path": str(target), "content": ""})
    assert target.read_bytes() == b""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,params,message",
    [
        ("read_file", {}, "Path parameter"),
        ("write_file", {}, "Path parameter"),
        ("write_file", {"path": "placeholder"}, "Content parameter"),
        ("list_directory", {}, "Path parameter"),
        ("search_files", {}, "Query parameter"),
        ("execute_command", {}, "Command parameter"),
    ],
)
async def test_missing_arguments(
    handler: MCPToolsHandler, method: str, params: dict[str, Any], message: str
) -> None:
    with pytest.raises(MCPToolError, match=message):
        await getattr(handler, method)(params)


@pytest.mark.asyncio
async def test_missing_wrong_kind_and_oversized_files(handler: MCPToolsHandler) -> None:
    root = handler.allowed_paths[0]
    for method in [handler.read_file, handler.list_directory, handler.search_files]:
        with pytest.raises(MCPToolError, match="does not exist"):
            await method({"path": str(root / "absent"), "query": "anything"})
    with pytest.raises(MCPToolError, match="not a file"):
        await handler.read_file({"path": str(root)})
    target = root / "large"
    with target.open("wb") as stream:
        stream.truncate(10 * 1024 * 1024 + 1)
    with pytest.raises(MCPToolError, match="too large"):
        await handler.read_file({"path": str(target)})
    with pytest.raises(MCPToolError, match="not a directory"):
        await handler.list_directory({"path": str(target)})
    with pytest.raises(MCPToolError, match="too large"):
        await handler.write_file(
            {"path": str(target), "content": "x" * (5 * 1024 * 1024 + 1)}
        )
    assert target.stat().st_size == 10 * 1024 * 1024 + 1
    assert (await handler.search_files({"path": str(root), "query": "large"}))[
        "results"
    ][0]["match_type"] == ["filename"]


@pytest.mark.asyncio
async def test_symlink_and_parent_traversal_refused(
    handler: MCPToolsHandler, tmp_path: Path
) -> None:
    root = handler.allowed_paths[0]
    outside = tmp_path / "private.txt"
    outside.write_text("private fixture")
    link = root / "linked.txt"
    link.symlink_to(outside)
    for path in [link, root / ".." / "private.txt"]:
        with pytest.raises(MCPToolError, match="Path not allowed"):
            await handler.read_file({"path": str(path)})
        with pytest.raises(MCPToolError, match="Path not allowed"):
            await handler.write_file({"path": str(path), "content": "replacement"})
    assert outside.read_text() == "private fixture"
    found = await handler.search_files({"path": str(root), "query": "private"})
    assert found["results"] == []


@pytest.mark.asyncio
async def test_read_decode_error_and_missing_metadata(handler: MCPToolsHandler) -> None:
    target = handler.allowed_paths[0] / "invalid.txt"
    target.write_bytes(b"\xff")
    with pytest.raises(MCPToolError, match="File read failed"):
        await handler.read_file({"path": str(target)})
    with pytest.raises(MCPToolError, match="File write failed"):
        await handler.write_file(
            {"path": str(target), "content": "data", "encoding": "invalid-codec"}
        )
    assert handler._get_file_info(target.parent / "missing")["type"] == "unknown"


@pytest.mark.asyncio
async def test_command_preserves_output_and_exit_status(
    handler: MCPToolsHandler,
) -> None:
    result = await handler.execute_command(
        {"command": "printf output; printf error >&2; exit 7"}
    )
    assert (result["stdout"], result["stderr"], result["return_code"]) == (
        "output",
        "error",
        7,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "command", ["sudo true", "rm -rf fixture", "curl example.invalid"]
)
async def test_disallowed_command_never_spawns(
    handler: MCPToolsHandler, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    spawn = AsyncMock()
    monkeypatch.setattr(asyncio, "create_subprocess_shell", spawn)
    with pytest.raises(MCPToolError, match="Dangerous command"):
        await handler.execute_command({"command": command})
    spawn.assert_not_called()


@pytest.mark.asyncio
async def test_command_timeout_reaps_process(
    handler: MCPToolsHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = Mock(
        communicate=AsyncMock(side_effect=asyncio.TimeoutError), wait=AsyncMock()
    )
    monkeypatch.setattr(
        asyncio, "create_subprocess_shell", AsyncMock(return_value=process)
    )
    with pytest.raises(MCPToolError, match="timed out"):
        await handler.execute_command({"command": "fixture", "timeout": 1})
    process.kill.assert_called_once()
    process.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_spawn_failure_and_tool_dispatch(
    handler: MCPToolsHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        asyncio,
        "create_subprocess_shell",
        AsyncMock(side_effect=OSError("spawn unavailable")),
    )
    with pytest.raises(MCPToolError, match="Command execution failed"):
        await handler.execute_command({"command": "fixture"})
    monkeypatch.setattr(
        mcp_tools,
        "TOOL_REGISTRY",
        {
            "fixture": AsyncMock(return_value={"value": 42}),
            "broken": AsyncMock(side_effect=RuntimeError("provider failed")),
        },
    )
    assert (await mcp_tools.execute_tool("fixture", {}))["result"] == {"value": 42}
    assert (await mcp_tools.execute_tool("unknown", {}))["status"] == "error"
    assert (await mcp_tools.execute_tool("broken", {}))["status"] == "error"
