"""Plugin lifecycle contracts against real modules and a disposable database."""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

import source.plugins
from source.plugins import plugin_loader as loader_module
from source.plugins.plugin_loader import PluginLoader

PLUGIN_SOURCE = """
from source.plugins.base_plugin import BasePlugin

class FixturePlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.started = False
        self.cleaned = False

    async def configure(self, config):
        self.config = config

    async def initialize(self):
        self.started = True

    async def cleanup(self):
        self.cleaned = True

    async def configure_mcp_server(self, config):
        self.server_config = config

    async def get_tools(self):
        return [{"name": "echo"}]

    async def execute(self, tool_name, parameters):
        if tool_name != "echo":
            raise ValueError("unknown tool")
        return {"success": True, "value": parameters["value"]}
"""


@pytest.fixture
def modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    directory = tmp_path / "plugins"
    directory.mkdir()
    (directory / "fixture_plugin.py").write_text(PLUGIN_SOURCE)
    (directory / "empty_plugin.py").write_text("VALUE = 1\n")
    (directory / "broken_plugin.py").write_text(
        "raise RuntimeError('fixture failure')\n"
    )
    (directory / "base_plugin.py").touch()
    monkeypatch.setattr(
        source.plugins, "__path__", [str(directory), *source.plugins.__path__]
    )
    yield directory
    for name in ["fixture_plugin", "empty_plugin", "broken_plugin"]:
        sys.modules.pop(f"source.plugins.{name}", None)


@pytest_asyncio.fixture
async def loader(
    modules: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[PluginLoader]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'plugins.db'}")
    from source.database import DatabaseManager

    manager = DatabaseManager()
    await manager.initialize()
    instance = PluginLoader(manager)
    instance.plugins_directory = modules
    try:
        yield instance
    finally:
        await manager.config.engine.dispose()


@pytest.mark.asyncio
async def test_discovery_and_isolated_failures(loader: PluginLoader) -> None:
    assert set(await loader.discover_plugins()) == {
        "fixture_plugin",
        "empty_plugin",
        "broken_plugin",
    }
    plugins = await loader.load_all_plugins()
    assert list(plugins) == ["fixture_plugin"]
    status = await loader.get_plugin_status()
    assert status["plugins_loaded"] == 1
    assert status["plugins_failed"] == 2
    assert status["last_load_time"] is not None
    assert status["plugins"][0]["tools_count"] == 1
    assert loader.db_manager is not None
    rows = await loader.db_manager.execute_query(
        "SELECT name, status FROM plugins ORDER BY name"
    )
    assert rows == [
        {"name": "broken_plugin", "status": "error"},
        {"name": "empty_plugin", "status": "error"},
        {"name": "fixture_plugin", "status": "active"},
    ]


@pytest.mark.asyncio
async def test_configuration_survives_reload_and_unload(loader: PluginLoader) -> None:
    assert loader.db_manager is not None
    db = loader.db_manager
    await db.execute_query(
        "INSERT INTO plugins (name, display_name, version, module_path, config, author)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            "fixture_plugin",
            "Fixture",
            "1.0.0",
            "source.plugins.fixture_plugin",
            json.dumps({"setting": "retained"}),
            "Fixture Author",
        ],
    )
    plugin = await loader.load_plugin("fixture_plugin")
    assert plugin is not None
    assert getattr(plugin, "started") is True
    assert getattr(plugin, "config") == {"setting": "retained"}
    assert await loader.reload_plugin("fixture_plugin") is True
    assert getattr(plugin, "cleaned") is True
    replacement = loader.loaded_plugins["fixture_plugin"]
    assert replacement is not plugin
    assert getattr(replacement, "config") == {"setting": "retained"}
    assert await loader.unload_plugin("fixture_plugin") is True
    assert getattr(replacement, "cleaned") is True
    rows = await db.execute_query(
        "SELECT status, config, author, load_count FROM plugins WHERE name = ?",
        ["fixture_plugin"],
    )
    assert rows == [
        {
            "status": "inactive",
            "config": json.dumps({"setting": "retained"}),
            "author": "Fixture Author",
            "load_count": 2,
        }
    ]
    assert await loader.unload_plugin("fixture_plugin") is False


@pytest.mark.asyncio
async def test_tool_routing_and_failure_isolation(
    loader: PluginLoader, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin = await loader.load_plugin("fixture_plugin")
    assert plugin is not None
    assert await loader.get_plugin_tools() == {"fixture_plugin": [{"name": "echo"}]}
    assert await loader.execute_plugin_tool(
        "fixture_plugin", "echo", {"value": 42}
    ) == {"success": True, "value": 42}
    assert (await loader.execute_plugin_tool("missing", "echo", {}))["success"] is False
    assert (await loader.execute_plugin_tool("fixture_plugin", "unknown", {}))[
        "success"
    ] is False
    monkeypatch.setattr(
        plugin, "get_tools", AsyncMock(side_effect=RuntimeError("catalog unavailable"))
    )
    assert await loader.get_plugin_tools() == {"fixture_plugin": []}


@pytest.mark.asyncio
async def test_cleanup_failure_preserves_loaded_instance(
    loader: PluginLoader, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin = await loader.load_plugin("fixture_plugin")
    assert plugin is not None
    monkeypatch.setattr(plugin, "cleanup", AsyncMock(side_effect=RuntimeError("busy")))
    assert await loader.reload_plugin("fixture_plugin") is False
    assert await loader.unload_plugin("fixture_plugin") is False
    assert loader.loaded_plugins["fixture_plugin"] is plugin


@pytest.mark.asyncio
async def test_failed_reload_reports_failure(
    loader: PluginLoader, monkeypatch: pytest.MonkeyPatch
) -> None:
    await loader.load_plugin("fixture_plugin")
    monkeypatch.setattr(loader, "load_plugin", AsyncMock(return_value=None))
    assert await loader.reload_plugin("fixture_plugin") is False
    assert "fixture_plugin" not in loader.loaded_plugins


@pytest.mark.asyncio
async def test_mcp_configuration_and_status(loader: PluginLoader) -> None:
    plugin = await loader.load_plugin("fixture_plugin")
    assert plugin is not None
    assert loader.db_manager is not None
    loader.loaded_plugins["firebase_mcp_plugin"] = plugin
    await loader.db_manager.execute_query(
        "INSERT INTO mcp_servers (name, display_name, server_type,"
        " communication_method, config, status) VALUES (?, ?, ?, ?, ?, ?)",
        [
            "fixture",
            "Fixture",
            "firebase",
            "http",
            json.dumps({"url": "https://example.invalid"}),
            "active",
        ],
    )
    await loader.load_mcp_server_plugins()
    assert getattr(plugin, "server_config") == {"url": "https://example.invalid"}
    status = await loader.get_plugin_status()
    assert status["mcp_servers"] == [
        {"name": "fixture", "status": "active", "plugin": "FixturePlugin"}
    ]
    assert status["mcp_servers_active"] == 1


@pytest.mark.asyncio
async def test_loader_without_database_and_global_initialization(
    modules: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader_module, "plugin_loader", None)
    monkeypatch.setattr(
        PluginLoader, "discover_plugins", AsyncMock(return_value=["fixture_plugin"])
    )
    first = await loader_module.get_plugin_loader()
    assert first.loaded_plugins["fixture_plugin"] is not None
    assert await loader_module.get_plugin_loader() is first
    await loader_module.initialize_plugins()
    second = await loader_module.get_plugin_loader()
    assert second is not first
    assert await second.unload_plugin("fixture_plugin") is True


@pytest.mark.asyncio
async def test_database_outage_does_not_hide_plugin_execution(
    loader: PluginLoader, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert loader.db_manager is not None
    monkeypatch.setattr(
        loader.db_manager,
        "execute_query",
        AsyncMock(side_effect=RuntimeError("database offline")),
    )
    assert await loader.load_plugin("fixture_plugin") is not None
    await loader.load_mcp_server_plugins()
    assert (
        await loader.execute_plugin_tool("fixture_plugin", "echo", {"value": "ok"})
    )["value"] == "ok"
