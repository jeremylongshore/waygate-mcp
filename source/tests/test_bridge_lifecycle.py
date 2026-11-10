"""Bridge lifecycle with local Python processes and modules, never providers."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from source.plugins.mcp_bridge_plugin import MCPBridgePlugin, MCPCommunicationError


class LocalBridge(MCPBridgePlugin):
    def __init__(self, command: list[str], config: dict[str, Any]) -> None:
        super().__init__(config)
        self.command = command

    async def get_mcp_server_command(self) -> list[str]:
        return self.command.copy()

    async def get_mcp_server_config(self) -> dict[str, Any]:
        return {}


@pytest.mark.asyncio
async def test_stdio_roundtrip_error_and_cleanup(tmp_path: Path) -> None:
    script = tmp_path / "stdio.py"
    script.write_text("""import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request['method'] == 'tools/list':
        response = {'result': {'tools': [{'name': 'echo'}]}}
    elif request['params']['name'] == 'error':
        response = {'error': {'message': 'fixture failure'}}
    else:
        response = {'result': request['params']['arguments']}
    print(json.dumps(response), flush=True)
""")
    bridge = LocalBridge(
        [sys.executable, str(script)], {"communication_method": "stdio"}
    )
    try:
        assert await bridge.get_tools() == [{"name": "echo"}]
        assert bridge.mcp_status["connected"] is True
        assert (await bridge.execute("echo", {"value": "fixture"}))["result"] == {
            "value": "fixture"
        }
        assert (await bridge.execute("error", {}))["success"] is False
        assert bridge.mcp_status["error_count"] == 1
    finally:
        await bridge.cleanup()
    assert bridge.process is not None and bridge.process.returncode is not None
    assert not bridge.is_initialized


@pytest.mark.asyncio
async def test_subprocess_argument_boundaries_and_text_output(tmp_path: Path) -> None:
    script = tmp_path / "cli.py"
    script.write_text("""import json, os, sys
if '--list-tools' in sys.argv:
    print(json.dumps({'tools': [{'name': 'echo'}]}))
elif 'error' in sys.argv:
    print('fixture failure', file=sys.stderr)
    sys.exit(3)
elif 'text' in sys.argv:
    print('plain output', end='')
else:
    print(json.dumps({'argv': sys.argv[1:], 'fixture': os.environ['FIXTURE_VALUE']}))
""")
    bridge = LocalBridge(
        [sys.executable, str(script)],
        {
            "communication_method": "subprocess",
            "credentials": {"fixture_value": "fixture-only"},
        },
    )
    assert (await bridge.execute("echo", {}))["success"] is False
    await bridge.initialize()
    value = "spaces; $(not-a-command)"
    result = await bridge.execute("echo", {"value": value})
    assert result["result"] == {
        "argv": ["--tool", "echo", "--value", value],
        "fixture": "fixture-only",
    }
    assert (await bridge.execute("text", {}))["result"] == {"output": "plain output"}
    assert (await bridge.execute("error", {}))["success"] is False
    assert bridge.get_info()["tool_count"] == 1
    await bridge.cleanup()


@pytest.mark.asyncio
async def test_python_initialize_reconfigure_and_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("waygate_fixture_provider")
    setattr(module, "get_tools", AsyncMock(return_value=[{"name": "echo"}]))
    setattr(module, "echo", lambda value: value)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    bridge = LocalBridge(
        [], {"communication_method": "python", "module_name": module.__name__}
    )
    await bridge.initialize()
    assert (await bridge.execute("echo", {"value": 5}))["result"] == 5
    await bridge.configure_mcp_server({"credentials": {"token": "fixture-only"}})
    assert bridge.is_initialized
    assert (await bridge._get_http_headers())["Authorization"] == "Token fixture-only"
    bridge.credentials = {"api_key": "fixture-only"}
    assert (await bridge._get_http_headers())["Authorization"] == "Bearer fixture-only"
    bridge.communication_method = "invalid"
    assert (await bridge.execute("echo", {}))["success"] is False
    await bridge.cleanup()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config",
    [
        {"communication_method": "http"},
        {"communication_method": "python"},
        {
            "communication_method": "python",
            "module_name": "waygate_fixture_module_does_not_exist",
        },
    ],
)
async def test_missing_transport_configuration_refuses(config: dict[str, Any]) -> None:
    bridge = LocalBridge([], config)
    with pytest.raises(MCPCommunicationError):
        await bridge.initialize()
    assert not bridge.is_initialized
    assert bridge.mcp_status["connected"] is False


@pytest.mark.asyncio
async def test_bad_provider_catalog_fails_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = ModuleType("waygate_malformed_provider")
    setattr(module, "get_tools", AsyncMock(return_value=[{"name": 17}]))
    monkeypatch.setitem(sys.modules, module.__name__, module)
    bridge = LocalBridge(
        [], {"communication_method": "python", "module_name": module.__name__}
    )
    with pytest.raises(MCPCommunicationError):
        await bridge.initialize()
    assert not bridge.is_initialized
    assert bridge.mcp_status["tool_count"] == 0


@pytest.mark.asyncio
async def test_failed_resync_clears_stale_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = LocalBridge([], {"communication_method": "python"})
    bridge.communication_method = "python"
    bridge.mcp_tools = [{"name": "stale"}]
    bridge.mcp_status["tool_count"] = 1
    monkeypatch.setattr(
        bridge, "_get_python_tools", AsyncMock(side_effect=RuntimeError("offline"))
    )
    with pytest.raises(MCPCommunicationError):
        await bridge._sync_mcp_tools()
    assert bridge.mcp_tools == []
    assert bridge.mcp_status["tool_count"] == 0


@pytest.mark.asyncio
async def test_cleanup_escalates_after_termination_timeout() -> None:
    bridge = LocalBridge([], {})
    process = Mock(wait=AsyncMock(side_effect=[asyncio.TimeoutError, 0]))
    bridge.process = process
    bridge.is_initialized = True
    await bridge.cleanup()
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    assert process.wait.await_count == 2
    assert not bridge.is_initialized


@pytest.mark.asyncio
async def test_stdio_missing_pipes_refuses() -> None:
    bridge = LocalBridge([], {})
    bridge.process = Mock(returncode=None, stdin=None, stdout=None)
    with pytest.raises(MCPCommunicationError, match="pipes"):
        await bridge._execute_stdio_tool("echo", {})
    with pytest.raises(MCPCommunicationError, match="pipes"):
        await bridge._get_stdio_tools()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "program", ["raise SystemExit(3)", "print('not JSON')", "print('{}')"]
)
async def test_subprocess_invalid_catalog_cannot_connect(program: str) -> None:
    bridge = LocalBridge(
        [sys.executable, "-c", program], {"communication_method": "subprocess"}
    )
    with pytest.raises(MCPCommunicationError):
        await bridge.initialize()
    assert not bridge.is_initialized
    assert not bridge.mcp_status["connected"]


@pytest.mark.asyncio
async def test_stdio_catalog_error_cannot_be_empty_success() -> None:
    bridge = LocalBridge([], {})
    bridge.process = Mock(
        returncode=None,
        stdin=Mock(drain=AsyncMock()),
        stdout=Mock(
            readline=AsyncMock(return_value=b'{"error":{"message":"denied"}}\n')
        ),
    )
    with pytest.raises(MCPCommunicationError, match="server error"):
        await bridge._get_stdio_tools()
