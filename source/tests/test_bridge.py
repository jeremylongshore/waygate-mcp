"""Bridge transports exercise typed state and reject malformed provider catalogs."""

from __future__ import annotations

import asyncio
from types import ModuleType
from typing import Any

import httpx
import pytest

from source.plugins.mcp_bridge_plugin import MCPBridgePlugin, MCPCommunicationError


class FixtureBridge(MCPBridgePlugin):
    async def get_mcp_server_command(self) -> list[str]:
        return []

    async def get_mcp_server_config(self) -> dict[str, Any]:
        return {}


@pytest.mark.asyncio
async def test_http_catalog_execute_and_cleanup() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path == "/tools":
            return httpx.Response(200, json={"tools": [{"name": "fixture"}]})
        return httpx.Response(200, json={"ok": True})

    bridge = FixtureBridge()
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://fixture"
    )
    bridge.mcp_client = client
    bridge.communication_method = "http"
    assert await bridge._get_http_tools() == [{"name": "fixture"}]
    result = await bridge._execute_http_tool("fixture", {"value": 1})
    assert result["result"] == {"ok": True}
    assert seen == ["/tools", "/tools/execute"]
    bridge.is_initialized = True
    bridge.mcp_status["connected"] = True
    await bridge.cleanup()
    assert client.is_closed
    assert not bridge.is_initialized
    assert bridge.mcp_status["connected"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [None, {}, ["bad"], [{"name": 12}], [{}]])
async def test_http_rejects_malformed_tools(value: object) -> None:
    bridge = FixtureBridge()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"tools": value})
        ),
        base_url="http://fixture",
    ) as client:
        bridge.mcp_client = client
        with pytest.raises(MCPCommunicationError, match="named objects"):
            await bridge._get_http_tools()


@pytest.mark.asyncio
async def test_transport_type_mismatch_refuses() -> None:
    bridge = FixtureBridge()
    bridge.mcp_client = "subprocess"
    with pytest.raises(MCPCommunicationError, match="HTTP MCP client"):
        await bridge._execute_http_tool("fixture", {})
    with pytest.raises(MCPCommunicationError, match="Python MCP client"):
        await bridge._execute_python_tool("fixture", {})
    assert await bridge._get_http_tools() == []
    assert await bridge._get_python_tools() == []
    with pytest.raises(MCPCommunicationError, match="not running"):
        await bridge._execute_stdio_tool("fixture", {})
    assert await bridge._get_stdio_tools() == []


@pytest.mark.asyncio
async def test_python_sync_async_tools_and_missing_tool() -> None:
    module = ModuleType("fixture_module")

    def sync_tool(value: int) -> int:
        return value + 1

    async def async_tool(value: int) -> int:
        return value + 2

    setattr(module, "sync_tool", sync_tool)
    setattr(module, "async_tool", async_tool)
    bridge = FixtureBridge()
    bridge.mcp_client = module
    assert (await bridge._execute_python_tool("sync_tool", {"value": 2}))["result"] == 3
    assert (await bridge._execute_python_tool("async_tool", {"value": 2}))[
        "result"
    ] == 4
    assert {tool["name"] for tool in await bridge._get_python_tools()} == {
        "sync_tool",
        "async_tool",
    }
    with pytest.raises(MCPCommunicationError, match="Tool not found"):
        await bridge._execute_python_tool("missing", {})


@pytest.mark.asyncio
async def test_unknown_transport_cannot_initialize() -> None:
    bridge = FixtureBridge({"communication_method": "invalid"})
    with pytest.raises(MCPCommunicationError, match="Unsupported communication"):
        await bridge.initialize()
    assert not bridge.is_initialized
    assert bridge.mcp_status["error_count"] == 1
    assert bridge.mcp_status["last_error"]


@pytest.mark.asyncio
async def test_request_timeout_is_reported_as_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from source.exceptions import MCPToolError
    from source.mcp_tools import MCPToolsHandler

    def timeout(*args: Any, **kwargs: Any) -> None:
        raise asyncio.TimeoutError()

    monkeypatch.setattr("source.mcp_tools.aiohttp.ClientSession", timeout)
    with pytest.raises(MCPToolError, match="Request timeout"):
        await MCPToolsHandler().http_request(
            {"url": "https://fixture.invalid", "timeout": 1}
        )
