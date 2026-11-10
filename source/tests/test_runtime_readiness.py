"""Provider startup must honor explicit enablement before any external activity."""

import importlib
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from source.plugins.plugin_loader import PluginLoader


@pytest.mark.asyncio
async def test_disabled_provider_is_never_initialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "false")
    module = importlib.import_module("source.mcp_integration")
    loader_module = importlib.import_module("source.plugins.plugin_loader")
    bridge_module = importlib.import_module("source.plugins.mcp_bridge_plugin")
    startup = AsyncMock(side_effect=AssertionError("external startup forbidden"))
    monkeypatch.setattr(bridge_module.MCPBridgePlugin, "initialize", startup)
    monkeypatch.setattr(loader_module, "plugin_loader", None)
    manager = module.MCPIntegrationManager()
    await manager.initialize()
    startup.assert_not_awaited()
    assert manager.plugin_loader.plugin_stats["total_failed"] == 0
    assert (await manager.get_mcp_status())["integration_status"] == "disabled"


@pytest.mark.asyncio
async def test_discovery_excludes_abstract_bridge_and_disabled_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
    names = await PluginLoader().discover_plugins()
    assert "mcp_bridge_plugin" not in names
    assert "firebase_mcp_plugin" not in names


@pytest.mark.asyncio
async def test_enabled_missing_provider_is_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "missing")
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "false")
    module = importlib.import_module("source.mcp_integration")
    monkeypatch.setattr(
        module, "get_plugin_loader", AsyncMock(return_value=PluginLoader())
    )
    monkeypatch.setattr(module, "list_mcp_servers", AsyncMock(return_value=[]))
    manager = module.MCPIntegrationManager()
    await manager.initialize()
    status = await manager.get_mcp_status()
    assert status["integration_status"] == "degraded"
    assert status["providers"] == {"missing": "failed"}


@pytest.mark.asyncio
async def test_health_probes_real_database_and_reports_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'health.db'}")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
    module = importlib.import_module("source.waygate_mcp")
    from httpx import ASGITransport, AsyncClient

    from source.database import DatabaseManager

    db = DatabaseManager()
    await db.initialize()
    monkeypatch.setattr(module, "db_manager", db)
    server = module.WaygateServer(
        module.WaygateSettings(
            WAYGATE_BASE_DIR=tmp_path,
            WAYGATE_DATA_DIR=tmp_path / "data",
            WAYGATE_PROJECTS_DIR=tmp_path / "projects",
        )
    )
    try:
        async with AsyncClient(
            transport=ASGITransport(app=server.app), base_url="http://test"
        ) as client:
            for route in ["/health", "/ready"]:
                result = await client.get(route)
                assert result.status_code == 200
                assert result.json()["checks"] == {
                    "database": "ok",
                    "providers": "disabled",
                }
            monkeypatch.setenv("MCP_SERVERS_ENABLED", "missing")
            result = await client.get("/ready")
            assert result.status_code == 503
            assert result.json()["ready"] is False
            assert result.json()["checks"]["provider:missing"] == "failed"
            monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
            monkeypatch.setattr(
                db,
                "execute_query",
                AsyncMock(side_effect=RuntimeError("private-token")),
            )
            for route in ["/health", "/ready"]:
                result = await client.get(route)
                assert result.status_code == 503
                assert result.json()["checks"]["database"] == "failed"
                assert "private-token" not in result.text
    finally:
        await db.config.engine.dispose()


@pytest.mark.asyncio
async def test_enabled_bridge_starts_only_after_configuration_and_reports_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import sys

    import source.plugins

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "fixture")
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "false")
    (tmp_path / "fixture_mcp_plugin.py").write_text("""
from source.plugins.mcp_bridge_plugin import MCPBridgePlugin
class FixtureBridge(MCPBridgePlugin):
    starts = []
    async def get_mcp_server_command(self):
        self.starts.append(self.mcp_config.get("configured"))
        raise RuntimeError("fixture provider startup failure")
    async def get_mcp_server_config(self):
        return {}
""")
    monkeypatch.setattr(
        source.plugins, "__path__", [str(tmp_path), *source.plugins.__path__]
    )
    module = importlib.import_module("source.mcp_integration")
    loader = PluginLoader()
    loader.plugins_directory = tmp_path
    await loader.load_all_plugins()
    plugin = loader.loaded_plugins["fixture_mcp_plugin"]
    assert getattr(plugin, "starts") == []
    monkeypatch.setattr(module, "get_plugin_loader", AsyncMock(return_value=loader))
    monkeypatch.setattr(
        module,
        "list_mcp_servers",
        AsyncMock(
            return_value=[
                {
                    "name": "fixture",
                    "server_type": "fixture",
                    "display_name": "Fixture",
                    "credentials": {},
                    "configured": True,
                }
            ]
        ),
    )
    monkeypatch.setattr(module, "update_mcp_server_status", AsyncMock())
    try:
        manager = module.MCPIntegrationManager()
        await manager.initialize()
        assert getattr(plugin, "starts") == [True]
        assert manager.provider_readiness() == {"fixture": "failed"}
        assert (await manager.get_mcp_status())["integration_status"] == "degraded"
        assert manager.mcp_servers == {}
    finally:
        sys.modules.pop("source.plugins.fixture_mcp_plugin", None)


def test_readiness_observes_provider_disconnect_without_restarting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "fixture")
    module = importlib.import_module("source.mcp_integration")
    manager = module.MCPIntegrationManager()
    manager.is_initialized = True
    plugin = SimpleNamespace(
        is_initialized=True,
        mcp_status={"connected": True},
        process=SimpleNamespace(returncode=None),
        get_tools=AsyncMock(),
    )
    manager.mcp_servers["fixture"] = {
        "config": {"server_type": "fixture"},
        "plugin": plugin,
        "status": "active",
    }
    assert manager.provider_readiness() == {"fixture": "ok"}
    plugin.process.returncode = 1
    assert manager.provider_readiness() == {"fixture": "failed"}
    plugin.process = None
    plugin.mcp_status["connected"] = False
    assert manager.provider_readiness() == {"fixture": "failed"}
    plugin.get_tools.assert_not_called()
