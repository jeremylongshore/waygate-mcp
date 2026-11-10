"""HTTP status, administration and metrics must reflect actual runtime effects."""

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from source.plugins.plugin_loader import PluginLoader


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> SimpleNamespace:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "")
    monkeypatch.setenv("MCP_AUTO_INITIALIZE", "false")
    module = importlib.import_module("source.waygate_mcp")
    integration = importlib.import_module("source.mcp_integration")
    loader = PluginLoader()
    manager = integration.MCPIntegrationManager()
    manager.plugin_loader = loader
    manager.is_initialized = True
    monkeypatch.setattr(module, "get_mcp_manager", AsyncMock(return_value=manager))
    settings = module.WaygateSettings(
        WAYGATE_BASE_DIR=tmp_path,
        WAYGATE_DATA_DIR=tmp_path / "data",
        WAYGATE_PROJECTS_DIR=tmp_path / "projects",
    )
    server = module.WaygateServer(settings)
    return SimpleNamespace(
        loader=loader,
        manager=manager,
        server=server,
        client=TestClient(server.app, raise_server_exceptions=False),
    )


def metric(client: TestClient, name: str) -> float:
    samples = [
        sample
        for family in text_string_to_metric_families(client.get("/metrics").text)
        for sample in family.samples
    ]
    return next(sample.value for sample in samples if sample.name == name)


def test_metrics_measure_requests_errors_and_durations(
    runtime: SimpleNamespace,
) -> None:
    client = runtime.client
    assert metric(client, "waygate_requests_total") == 0
    assert client.get("/").status_code == 200
    assert client.get("/missing-fixture").status_code == 404
    assert metric(client, "waygate_requests_total") == 2
    assert metric(client, "waygate_errors_total") == 1
    assert metric(client, "waygate_response_time_seconds_count") == 2
    assert metric(client, "waygate_response_time_seconds_sum") > 0


@pytest.mark.asyncio
async def test_status_listing_and_reload_use_real_registry(
    runtime: SimpleNamespace,
) -> None:
    old = await runtime.loader.load_plugin("github_plugin")
    assert old is not None
    setattr(old, "cleanup", AsyncMock())
    listed = runtime.client.get("/plugins").json()
    assert listed["total"] == 1
    assert listed["plugins"][0]["name"] == old.name
    status = runtime.client.get("/mcp/status").json()
    assert status["plugins_loaded"] == 1
    assert "read_file" in status["commands_available"]
    result = runtime.client.post("/plugins/reload")
    assert result.status_code == 200
    assert result.json()["count"] == 1
    assert runtime.loader.loaded_plugins["github_plugin"] is not old
    getattr(old, "cleanup").assert_awaited_once()


@pytest.mark.asyncio
async def test_reload_failure_is_not_success(runtime: SimpleNamespace) -> None:
    old = await runtime.loader.load_plugin("github_plugin")
    assert old is not None
    setattr(old, "cleanup", AsyncMock(side_effect=RuntimeError("private-token")))
    result = runtime.client.post("/plugins/reload")
    assert result.status_code == 503
    assert result.json()["count"] == 0
    assert result.json()["failed"] == ["github_plugin"]
    assert "private-token" not in result.text


@pytest.mark.asyncio
async def test_failed_catalog_remains_visible(runtime: SimpleNamespace) -> None:
    plugin = await runtime.loader.load_plugin("github_plugin")
    plugin.get_tools = AsyncMock(side_effect=RuntimeError("private-token"))
    result = runtime.client.get("/plugins")
    assert result.status_code == 200
    assert result.json()["plugins"][0]["status"] == "error"
    assert result.json()["plugins"][0]["tools_count"] is None
    assert "private-token" not in result.text


@pytest.mark.asyncio
async def test_provider_reload_replaces_routing_reference(
    runtime: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    from source.plugins.github_plugin import GitHubPlugin

    module = importlib.import_module("source.mcp_integration")
    monkeypatch.setenv("MCP_SERVERS_ENABLED", "fixture")
    old, new = GitHubPlugin(), GitHubPlugin()
    config = {
        "name": "fixture-server",
        "server_type": "fixture",
        "credentials": {},
        "display_name": "Fixture",
    }
    runtime.loader.loaded_plugins["fixture_mcp_plugin"] = old
    runtime.manager.mcp_servers["fixture-server"] = {
        "config": config,
        "plugin": old,
        "status": "active",
    }
    runtime.loader.mcp_servers["fixture-server"] = {"plugin": old}

    async def replace(name: str) -> bool:
        runtime.loader.loaded_plugins[name] = new
        return True

    monkeypatch.setattr(runtime.loader, "reload_plugin", replace)
    monkeypatch.setattr(module, "list_mcp_servers", AsyncMock(return_value=[config]))
    monkeypatch.setattr(module, "update_mcp_server_status", AsyncMock())
    result = await runtime.manager.reload_plugins()
    assert result["count"] == 1 and not result["failed"]
    assert runtime.manager.mcp_servers["fixture-server"]["plugin"] is new
    assert runtime.loader.mcp_servers["fixture-server"]["plugin"] is new
    new.get_tools = AsyncMock(side_effect=RuntimeError("provider down"))
    result = await runtime.manager.reload_plugins()
    assert result["failed"] == ["fixture_mcp_plugin"]
    assert not runtime.manager.mcp_servers


@pytest.mark.asyncio
async def test_disabled_provider_reload_unloads_instead_of_starting(
    runtime: SimpleNamespace,
) -> None:
    from source.plugins.github_plugin import GitHubPlugin

    plugin = GitHubPlugin()
    cleanup = AsyncMock()
    setattr(plugin, "cleanup", cleanup)
    runtime.loader.loaded_plugins["fixture_mcp_plugin"] = plugin
    runtime.manager.mcp_servers["fixture"] = {
        "config": {"server_type": "fixture"},
        "plugin": plugin,
        "status": "active",
    }
    result = await runtime.manager.reload_plugins()
    assert result["disabled"] == ["fixture_mcp_plugin"]
    assert not result["reloaded"] and not result["failed"]
    assert not runtime.loader.loaded_plugins and not runtime.manager.mcp_servers
    cleanup.assert_awaited_once()


def test_metrics_capture_unhandled_errors_and_isolate_servers(
    runtime: SimpleNamespace,
) -> None:
    async def crash() -> None:
        raise RuntimeError("private-token")

    runtime.server.app.add_api_route("/fixture-crash", crash)
    assert runtime.client.get("/fixture-crash").status_code == 500
    assert metric(runtime.client, "waygate_errors_total") == 1
    module = importlib.import_module("source.waygate_mcp")
    other = TestClient(module.WaygateServer(runtime.server.settings).app)
    assert metric(other, "waygate_requests_total") == 0
