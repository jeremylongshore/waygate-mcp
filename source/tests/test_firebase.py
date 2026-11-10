"""Firebase adapter contracts with a mocked MCP bridge; no cloud writes."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from source.plugins.firebase_mcp_plugin import FirebaseMCPPlugin
from source.plugins.mcp_bridge_plugin import MCPBridgePlugin


@pytest.fixture
def firebase(monkeypatch: pytest.MonkeyPatch) -> tuple[FirebaseMCPPlugin, AsyncMock]:
    for name in [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_STAGING_PROJECT_ID",
        "FIREBASE_REGION",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ]:
        monkeypatch.delenv(name, raising=False)
    bridge = AsyncMock(return_value={"success": True, "result": {"fixture": 42}})
    monkeypatch.setattr(MCPBridgePlugin, "execute", bridge)
    return FirebaseMCPPlugin(), bridge


@pytest.mark.asyncio
async def test_credentials_and_initialization(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin, _ = firebase
    initialize = AsyncMock()
    monkeypatch.setattr(MCPBridgePlugin, "initialize", initialize)
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "fixture-project")
    monkeypatch.setenv("FIREBASE_REGION", "fixture-region")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fixture/credentials.json")
    await plugin.initialize()
    initialize.assert_awaited_once()
    config = await plugin.get_mcp_server_config()
    assert config["project_id"] == "fixture-project"
    assert config["service_account_path"] == "/fixture/credentials.json"
    assert plugin.mcp_config["credentials"]["FIREBASE_REGION"] == "fixture-region"
    assert plugin.get_info()["firebase_project"] == "fixture-project"
    assert "mcp" in await plugin.get_mcp_server_command()


@pytest.mark.asyncio
async def test_default_credential_configuration(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock],
) -> None:
    plugin, _ = firebase
    await plugin._load_firebase_credentials()
    config = await plugin.get_mcp_server_config()
    assert plugin.credentials["FIREBASE_PROJECT_ID"] == config["project_id"]
    assert plugin.credentials["GOOGLE_APPLICATION_CREDENTIALS"] is None


@pytest.mark.asyncio
async def test_tool_enrichment_does_not_mutate_provider_catalog(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin, _ = firebase
    names = [
        "firebase_auth_list_users",
        "firebase_firestore_get",
        "firebase_firestore_set",
        "firebase_functions_deploy",
        "firebase_hosting_deploy",
        "other",
    ]
    catalog = [{"name": name, "description": "Fixture"} for name in names]
    monkeypatch.setattr(MCPBridgePlugin, "get_tools", AsyncMock(return_value=catalog))
    tools = await plugin.get_tools()
    assert len(tools) == len(names) + 4
    assert all(tool["category"] == "firebase" for tool in tools[: len(names)])
    assert all(tool["description"] == "Fixture" for tool in catalog)
    assert "use_case" not in tools[5]
    assert all("use_case" in tool for tool in tools[:5])
    assert len({tool["name"] for tool in tools}) == len(tools)


@pytest.mark.asyncio
async def test_standard_tool_success_failure_and_exception(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock],
) -> None:
    plugin, bridge = firebase
    plugin.credentials["FIREBASE_PROJECT_ID"] = "fixture-project"
    result = await plugin.execute("firebase_auth_list_users", {"limit": 2})
    assert result["context"]["project_id"] == "fixture-project"
    bridge.assert_awaited_once_with("firebase_auth_list_users", {"limit": 2})
    bridge.return_value = {"success": False, "error": "denied"}
    assert await plugin.execute("firebase_auth_list_users", {}) == {
        "success": False,
        "error": "denied",
    }
    bridge.side_effect = RuntimeError("provider offline")
    assert (await plugin.execute("firebase_auth_list_users", {}))["success"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("success", [True, False])
async def test_submission_and_analytics_routing(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock], success: bool
) -> None:
    plugin, bridge = firebase
    bridge.return_value = {"success": success, "result": {"fixture": 42}}
    result = await plugin.execute(
        "diagnosticpro_get_submission", {"submission_id": "fixture-id"}
    )
    assert result["success"] is success
    assert result["submission_id"] == "fixture-id"
    bridge.assert_awaited_with(
        "firebase_firestore_get",
        {"collection": "diagnosticSubmissions", "document": "fixture-id"},
    )
    result = await plugin.execute(
        "diagnosticpro_get_analytics", {"metric": "users", "date_range": "30d"}
    )
    assert result["success"] is success
    assert result["metric"] == "users"
    assert bridge.call_args.args[1]["where"] == [
        ["metric", "==", "users"],
        ["dateRange", "==", "30d"],
    ]
    assert bridge.call_args.args[1]["limit"] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("success", [True, False])
async def test_order_payload_and_provider_result(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock], success: bool
) -> None:
    plugin, bridge = firebase
    bridge.return_value = {"success": success}
    order = {
        "customer_email": "fixture@example.invalid",
        "equipment_type": "fixture",
        "issue_description": "test issue",
    }
    original = order.copy()
    result = await plugin.execute("diagnosticpro_create_order", order)
    assert result["success"] is success
    assert order == original
    tool, request = bridge.call_args.args
    assert tool == "firebase_firestore_set"
    assert request["collection"] == "orders"
    assert request["data"]["id"] == request["document"]
    assert request["data"]["customerEmail"] == original["customer_email"]
    assert request["data"]["status"] == "pending"
    assert request["data"]["paymentIntentId"] is None
    if success:
        assert result["order_id"] == request["document"]
    else:
        assert result["order_data"] == original


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "function_name,only",
    [("all", "functions"), ("analyze_diagnostic", "functions:analyze_diagnostic")],
)
@pytest.mark.parametrize("success", [True, False])
async def test_deployment_request_mapping_without_external_execution(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock],
    function_name: str,
    only: str,
    success: bool,
) -> None:
    plugin, bridge = firebase
    plugin.credentials["FIREBASE_PROJECT_ID"] = "fixture-project"
    bridge.return_value = {"success": success, "result": {"fixture": True}}
    result = await plugin.execute(
        "diagnosticpro_deploy_functions",
        {"function_name": function_name, "environment": "production"},
    )
    assert result["success"] is success
    bridge.assert_awaited_once_with(
        "firebase_functions_deploy", {"only": only, "project": "fixture-project"}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool,params",
    [
        ("diagnosticpro_unknown", {}),
        ("diagnosticpro_get_submission", {}),
        ("diagnosticpro_create_order", {}),
        ("diagnosticpro_deploy_functions", {"function_name": "unknown"}),
    ],
)
async def test_invalid_custom_request_never_reaches_provider(
    firebase: tuple[FirebaseMCPPlugin, AsyncMock], tool: str, params: dict[str, Any]
) -> None:
    plugin, bridge = firebase
    assert (await plugin.execute(tool, params))["success"] is False
    bridge.assert_not_awaited()
