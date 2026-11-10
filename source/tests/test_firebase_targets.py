"""Deployment requests must select an explicit, unambiguous Firebase project."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from source.plugins.firebase_mcp_plugin import FirebaseMCPPlugin
from source.plugins.mcp_bridge_plugin import MCPBridgePlugin


@pytest.fixture
def target_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FirebaseMCPPlugin, AsyncMock]:
    for name in [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_STAGING_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ]:
        monkeypatch.delenv(name, raising=False)
    bridge = AsyncMock(return_value={"success": True, "result": {"fixture": True}})
    monkeypatch.setattr(MCPBridgePlugin, "execute", bridge)
    return FirebaseMCPPlugin(), bridge


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "environment,key",
    [("staging", "FIREBASE_STAGING_PROJECT_ID"), ("production", "FIREBASE_PROJECT_ID")],
)
async def test_each_environment_uses_its_explicit_project(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock],
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
    key: str,
) -> None:
    plugin, bridge = target_plugin
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "fixture-production")
    monkeypatch.setenv("FIREBASE_STAGING_PROJECT_ID", "fixture-staging")
    await plugin._load_firebase_credentials()
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": "all", "environment": environment},
    )
    assert result["success"] is True
    bridge.assert_awaited_once_with(
        "firebase_functions_deploy",
        {"only": "functions", "project": plugin.credentials[key]},
    )
    assert result["project_id"] == f"fixture-{environment}"


@pytest.mark.asyncio
async def test_default_staging_never_inherits_production(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin, bridge = target_plugin
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "fixture-production")
    await plugin._load_firebase_credentials()
    result = await plugin.execute(
        "diagnosticpro_deploy_functions", {"function_name": "all"}
    )
    assert result["success"] is False
    bridge.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["staging", "production"])
async def test_absent_configuration_never_uses_hardcoded_project(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock], environment: str
) -> None:
    plugin, bridge = target_plugin
    await plugin._load_firebase_credentials()
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": "all", "environment": environment},
    )
    assert result["success"] is False
    bridge.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["prod", "invalid", "", None, 1, ["staging"]])
async def test_invalid_environment_never_reaches_provider(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock], environment: Any
) -> None:
    plugin, bridge = target_plugin
    plugin.credentials = {
        "FIREBASE_PROJECT_ID": "fixture-production",
        "FIREBASE_STAGING_PROJECT_ID": "fixture-staging",
    }
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": "all", "environment": environment},
    )
    assert result["success"] is False
    bridge.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [None, "", "   ", 42])
@pytest.mark.parametrize(
    "environment,key",
    [("staging", "FIREBASE_STAGING_PROJECT_ID"), ("production", "FIREBASE_PROJECT_ID")],
)
async def test_empty_or_invalid_target_never_reaches_provider(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock],
    value: Any,
    environment: str,
    key: str,
) -> None:
    plugin, bridge = target_plugin
    plugin.credentials[key] = value
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": "all", "environment": environment},
    )
    assert result["success"] is False
    bridge.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["staging", "production"])
async def test_shared_project_is_rejected(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock], environment: str
) -> None:
    plugin, bridge = target_plugin
    plugin.credentials = {
        "FIREBASE_PROJECT_ID": "fixture-shared",
        "FIREBASE_STAGING_PROJECT_ID": " fixture-shared ",
    }
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": "all", "environment": environment},
    )
    assert result["success"] is False
    bridge.assert_not_awaited()


@pytest.mark.asyncio
async def test_catalog_declares_environment_choices(
    target_plugin: tuple[FirebaseMCPPlugin, AsyncMock],
) -> None:
    plugin, _ = target_plugin
    tools = await plugin._get_diagnosticpro_tools()
    deployment = next(
        tool for tool in tools if tool["name"] == "diagnosticpro_deploy_functions"
    )
    assert deployment["inputSchema"]["properties"]["environment"]["enum"] == [
        "staging",
        "production",
    ]
