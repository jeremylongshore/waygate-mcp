"""MCP integration lifecycle with controlled provider and database boundaries."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from source.plugins.base_plugin import BasePlugin
from source.plugins.plugin_loader import PluginLoader


@pytest.fixture
def integration(monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, Any, Mock]:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "false")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "firebase")
    module = importlib.import_module("source.mcp_integration")
    plugin = Mock(spec=BasePlugin)
    plugin.get_tools = AsyncMock(return_value=[{"name": "echo"}])
    plugin.execute = AsyncMock(return_value={"success": True, "value": 42})
    plugin.get_info.return_value = {"name": "Fixture"}
    plugin.configure_mcp_server = AsyncMock()
    loader = PluginLoader()
    loader.loaded_plugins["firebase_mcp_plugin"] = plugin
    monkeypatch.setattr(module, "get_plugin_loader", AsyncMock(return_value=loader))
    monkeypatch.setattr(
        module,
        "list_mcp_servers",
        AsyncMock(
            return_value=[
                {
                    "name": "fixture",
                    "display_name": "Fixture",
                    "server_type": "firebase",
                    "credentials": {},
                    "config": {},
                }
            ]
        ),
    )
    monkeypatch.setattr(module, "update_mcp_server_status", AsyncMock())
    monkeypatch.setattr(module, "initialize_default_mcp_servers", AsyncMock())
    manager = module.MCPIntegrationManager()
    monkeypatch.setattr(
        manager, "_load_mcp_credentials", AsyncMock(return_value={"fixture": "value"})
    )
    return module, manager, plugin


@pytest.mark.asyncio
async def test_initialize_route_status_reload_and_global_accessor(
    integration: tuple[ModuleType, Any, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    module, manager, plugin = integration
    assert (await manager.get_mcp_status())["integration_status"] == "inactive"
    monkeypatch.setattr(module, "mcp_integration_manager", manager)
    await module.initialize_mcp_integration()
    assert await module.get_mcp_manager() is manager
    assert await manager.get_all_mcp_tools() == {"fixture": [{"name": "echo"}]}
    assert (await manager.execute_mcp_tool("fixture", "echo", {"value": 42}))[
        "mcp_server"
    ] == "fixture"
    plugin.execute.assert_awaited_once_with("echo", {"value": 42})
    status = await manager.get_mcp_status()
    assert (status["active_servers"], status["total_tools"]) == (1, 1)
    assert await manager.reload_mcp_server("fixture") is True
    assert await manager.reload_mcp_server("missing") is False
    assert (await manager.execute_mcp_tool("missing", "echo", {}))[
        "available_servers"
    ] == ["fixture"]


@pytest.mark.asyncio
async def test_provider_failures_are_reported(
    integration: tuple[ModuleType, Any, Mock],
) -> None:
    _, manager, plugin = integration
    await manager.initialize()
    plugin.execute.side_effect = RuntimeError("provider unavailable")
    assert (await manager.execute_mcp_tool("fixture", "echo", {}))["success"] is False
    plugin.get_tools.side_effect = RuntimeError("catalog unavailable")
    assert await manager.get_all_mcp_tools() == {"fixture": []}
    status = await manager.get_mcp_status()
    assert status["active_servers"] == 0
    assert status["servers"][0]["status"] == "error"


@pytest.mark.asyncio
async def test_failed_reload_does_not_report_active_success(
    integration: tuple[ModuleType, Any, Mock],
) -> None:
    module, manager, plugin = integration
    await manager.initialize()
    plugin.get_tools.side_effect = RuntimeError("catalog unavailable")
    assert await manager.reload_mcp_server("fixture") is False
    assert "fixture" not in manager.mcp_servers
    assert module.update_mcp_server_status.call_args.args[1] == "error"


@pytest.mark.asyncio
async def test_database_failure_before_config_does_not_mask_original_error(
    integration: tuple[ModuleType, Any, Mock],
) -> None:
    module, manager, _ = integration
    module.list_mcp_servers.side_effect = RuntimeError("database unavailable")
    await manager._load_mcp_server("firebase")
    assert manager.mcp_servers == {}
    module.update_mcp_server_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_plugin_and_missing_configuration(
    integration: tuple[ModuleType, Any, Mock],
) -> None:
    module, manager, _ = integration
    module.get_plugin_loader.return_value.loaded_plugins.clear()
    await manager.initialize()
    assert manager.mcp_servers == {}
    assert module.update_mcp_server_status.call_args.args[1] == "error"
    module.list_mcp_servers.return_value = []
    module.update_mcp_server_status.reset_mock()
    await manager._load_mcp_server("firebase")
    module.update_mcp_server_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_default_seed_only_when_empty_and_auto_enabled(
    integration: tuple[ModuleType, Any, Mock], monkeypatch: pytest.MonkeyPatch
) -> None:
    module, manager, _ = integration
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "true")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
    module.list_mcp_servers.return_value = []
    await manager.initialize()
    module.initialize_default_mcp_servers.assert_awaited_once()
    module.list_mcp_servers.return_value = [{"name": "existing"}]
    await manager.initialize()
    module.initialize_default_mcp_servers.assert_awaited_once()
    module.get_plugin_loader.side_effect = RuntimeError("loader unavailable")
    with pytest.raises(RuntimeError, match="loader unavailable"):
        await manager.initialize()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server_type,keys",
    [
        (
            "firebase",
            [
                "FIREBASE_PROJECT_ID",
                "FIREBASE_STAGING_PROJECT_ID",
                "FIREBASE_REGION",
                "GOOGLE_APPLICATION_CREDENTIALS",
            ],
        ),
        (
            "bigquery",
            [
                "GOOGLE_CLOUD_PROJECT",
                "BIGQUERY_DATASET",
                "GOOGLE_APPLICATION_CREDENTIALS",
            ],
        ),
        ("github", ["GITHUB_TOKEN", "GITHUB_OWNER"]),
        ("n8n", ["N8N_API_URL", "N8N_API_KEY"]),
        ("docker_hub", ["DOCKER_HUB_TOKEN", "DOCKER_HUB_USERNAME"]),
        ("slack", ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_WORKSPACE"]),
        ("unknown", []),
    ],
)
async def test_credentials_filter_absent_values(
    integration: tuple[ModuleType, Any, Mock],
    monkeypatch: pytest.MonkeyPatch,
    server_type: str,
    keys: list[str],
) -> None:
    module, _, _ = integration
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    manager = module.MCPIntegrationManager()
    assert await manager._load_mcp_credentials(server_type) == {}
    if keys:
        monkeypatch.setenv(keys[0], "fixture-only")
        assert await manager._load_mcp_credentials(server_type) == {
            keys[0]: "fixture-only"
        }
