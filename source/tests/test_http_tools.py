"""HTTP transport contracts without live network requests or credentials."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from source import mcp_tools
from source.exceptions import MCPToolError
from source.mcp_tools import MCPToolsHandler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body,parsed",
    [('{"value":42}', {"value": 42}), ("plain text", "plain text"), ("", None)],
)
async def test_http_response_preserves_status_headers_and_payload(
    monkeypatch: pytest.MonkeyPatch, body: str, parsed: Any
) -> None:
    response = Mock(status=418, headers={"Content-Type": "fixture"})
    response.text = AsyncMock(return_value=body)
    response.json = AsyncMock(return_value=parsed)
    if parsed == "plain text":
        response.json.side_effect = ValueError("not JSON")
    request_context = AsyncMock()
    request_context.__aenter__.return_value = response
    session = Mock(request=Mock(return_value=request_context))
    context = AsyncMock()
    context.__aenter__.return_value = session
    factory = Mock(return_value=context)
    monkeypatch.setattr(mcp_tools.aiohttp, "ClientSession", factory)
    result = await MCPToolsHandler().http_request(
        {
            "url": "https://example.invalid/api",
            "method": "post",
            "headers": {"X-Fixture": "yes"},
            "json": {"input": 1},
            "timeout": 4,
        }
    )
    assert result["status_code"] == 418
    assert result["data"] == parsed
    assert result["headers"] == {"Content-Type": "fixture"}
    assert result["method"] == "POST"
    session.request.assert_called_once_with(
        method="POST",
        url="https://example.invalid/api",
        headers={"X-Fixture": "yes"},
        json={"input": 1},
        data=None,
    )
    assert factory.call_args.kwargs["timeout"].total == 4
    context.__aexit__.assert_awaited_once()
    request_context.__aexit__.assert_awaited_once()
    if not body:
        response.json.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,message",
    [
        ({}, "URL parameter"),
        ({"url": "http://example.invalid"}, "Only HTTPS"),
        ({"url": "file:///fixture"}, "Only HTTPS"),
    ],
)
async def test_invalid_http_input_never_opens_transport(
    monkeypatch: pytest.MonkeyPatch, params: dict[str, Any], message: str
) -> None:
    factory = Mock()
    monkeypatch.setattr(mcp_tools.aiohttp, "ClientSession", factory)
    with pytest.raises(MCPToolError, match=message):
        await MCPToolsHandler().http_request(params)
    factory.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error,message",
    [
        (aiohttp.ClientConnectionError("offline"), "HTTP client error"),
        (RuntimeError("transport unavailable"), "HTTP request failed"),
    ],
)
async def test_transport_errors_are_tool_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception, message: str
) -> None:
    context = AsyncMock()
    context.__aenter__.side_effect = error
    monkeypatch.setattr(mcp_tools.aiohttp, "ClientSession", Mock(return_value=context))
    with pytest.raises(MCPToolError, match=message):
        await MCPToolsHandler().http_request({"url": "https://example.invalid"})
