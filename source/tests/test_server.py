"""HTTP and settings contracts without external providers or a listening socket."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.delenv("WAYGATE_SECRET_KEY", raising=False)
    module = importlib.import_module("source.waygate_mcp")
    settings = module.WaygateSettings(
        WAYGATE_DATA_DIR=tmp_path / "data",
        WAYGATE_PROJECTS_DIR=tmp_path / "projects",
        WAYGATE_BASE_DIR=tmp_path,
        WAYGATE_HOST="127.0.0.1",
    )
    manager = SimpleNamespace(
        mcp_servers={},
        get_mcp_status=AsyncMock(return_value={"status": "ready"}),
        get_all_mcp_tools=AsyncMock(return_value={}),
        execute_mcp_tool=AsyncMock(return_value={"success": True}),
        reload_mcp_server=AsyncMock(return_value=False),
    )
    monkeypatch.setattr(module, "get_mcp_manager", AsyncMock(return_value=manager))
    app = module.WaygateServer(settings).app
    return SimpleNamespace(
        module=module,
        settings=settings,
        manager=manager,
        client=TestClient(app, raise_server_exceptions=False),
    )


def test_settings_generate_secret_and_create_only_configured_directories(
    server: SimpleNamespace,
) -> None:
    assert len(server.settings.secret_key) == 64
    assert server.settings.data_dir.is_dir()
    assert server.settings.projects_dir.is_dir()
    assert server.settings.host == "127.0.0.1"


def test_runtime_reports_reviewed_release_version(server: SimpleNamespace) -> None:
    from source.version import VERSION

    assert server.client.get("/health").json()["version"] == VERSION
    assert server.client.get("/").json()["version"] == VERSION
    assert server.client.get("/openapi.json").json()["info"]["version"] == VERSION


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/health",
        "/ready",
        "/metrics",
        "/mcp/status",
        "/plugins",
        "/mcp/servers",
        "/mcp/tools",
        "/diagnostics/connection",
        "/diagnostics/performance",
    ],
)
def test_supported_routes_return_success(server: SimpleNamespace, path: str) -> None:
    assert server.client.get(path).status_code == 200


def test_http_validation_failures_keep_their_status(server: SimpleNamespace) -> None:
    response = server.client.post("/mcp/tools/execute", json={})
    assert response.status_code == 400
    assert response.json()["error"]["status_code"] == 400
    response = server.client.post("/mcp/servers/unknown/reload")
    assert response.status_code == 400
    response = server.client.get("/mcp/servers/unknown/tools")
    assert response.status_code == 404
    assert response.json()["error"]["status_code"] == 404


def test_provider_failure_is_a_server_error(server: SimpleNamespace) -> None:
    server.manager.execute_mcp_tool.side_effect = RuntimeError("fixture failure")
    response = server.client.post(
        "/mcp/tools/execute", json={"server_name": "fixture", "tool_name": "read"}
    )
    assert response.status_code == 500


def test_command_failure_has_a_valid_response_model(
    server: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        server.module, "execute_tool", AsyncMock(side_effect=RuntimeError("failure"))
    )
    response = server.client.post("/mcp/execute", json={"action": "read"})
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["result"] is None
    assert response.json()["error"] == "failure"


def test_command_success_and_external_tools(
    server: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        server.module,
        "execute_tool",
        AsyncMock(return_value={"status": "success", "result": {"data": 1}}),
    )
    assert server.client.post("/mcp/execute", json={"action": "read"}).json()[
        "result"
    ] == {"data": 1}
    server.manager.get_all_mcp_tools.return_value = {"fixture": [{"name": "remote"}]}
    response = server.client.get("/mcp/tools").json()
    assert any(tool["name"] == "remote" for tool in response["all_tools"])
    server.manager.reload_mcp_server.return_value = True
    assert server.client.post("/mcp/servers/fixture/reload").status_code == 200
    assert server.client.post("/plugins/reload").status_code == 200


def test_external_catalog_failure_preserves_local_tools(
    server: SimpleNamespace,
) -> None:
    server.manager.get_all_mcp_tools.side_effect = RuntimeError("unavailable")
    response = server.client.get("/mcp/tools")
    assert response.status_code == 200
    assert response.json()["local_tools"]
    assert response.json()["external_tools"] == {}


@pytest.mark.asyncio
async def test_http_handler_falls_back_for_unexpected_exception(
    server: SimpleNamespace,
) -> None:
    from starlette.requests import Request

    instance = server.module.WaygateServer(server.settings)
    request = Request({"type": "http"})
    response = await instance._http_exception_handler(request, RuntimeError("private"))
    assert response.status_code == 500
    assert b"private" not in response.body
    response = await instance._http_exception_handler(
        request, HTTPException(409, "conflict")
    )
    assert response.status_code == 409
