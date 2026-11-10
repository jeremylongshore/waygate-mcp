"""X adapter request/response handling using fake credentials and transport."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from source import x_twitter_integration as twitter
from source.exceptions import MCPToolError


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> twitter.XTwitterAPI:
    for name in [
        "X_BEARER_TOKEN",
        "TWITTER_BEARER_TOKEN",
        "X_API_BEARER_TOKEN",
        "TWITTER_API_BEARER_TOKEN",
        "X_OAUTH2_ACCESS_TOKEN",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        twitter.XTwitterAPI, "_check_oauth1a_availability", lambda self: False
    )
    monkeypatch.setenv("X_BEARER_TOKEN", "fixture-only")
    return twitter.XTwitterAPI()


def transport(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    payload: dict[str, Any],
    text: str | None = None,
) -> Mock:
    response = Mock(
        status=status,
        json=AsyncMock(return_value=payload),
        text=AsyncMock(return_value=json.dumps(payload) if text is None else text),
    )
    response_context = AsyncMock()
    response_context.__aenter__.return_value = response
    session = Mock(
        get=Mock(return_value=response_context),
        post=Mock(return_value=response_context),
    )
    context = AsyncMock()
    context.__aenter__.return_value = session
    monkeypatch.setattr(twitter.aiohttp, "ClientSession", Mock(return_value=context))
    return session


@pytest.mark.asyncio
async def test_post_payload_and_wrappers(
    api: twitter.XTwitterAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = transport(monkeypatch, 201, {"data": {"id": "fixture-id"}})
    monkeypatch.setattr(twitter, "x_api", api)
    result = await twitter.post_tweet_tool(
        {
            "text": "fixture",
            "reply_to_id": "parent",
            "poll": {"options": ["a", "b"]},
            "media_ids": ["image"],
        }
    )
    assert result["tweet_id"] == "fixture-id"
    assert result["url"].endswith("/fixture-id")
    assert session.post.call_args.kwargs["json"] == {
        "text": "fixture",
        "reply": {"in_reply_to_tweet_id": "parent"},
        "poll": {"options": ["a", "b"]},
        "media": {"media_ids": ["image"]},
    }
    assert (
        session.post.call_args.kwargs["headers"]["Authorization"]
        == "Bearer fixture-only"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,payload,expected",
    [
        (401, {}, "Authentication"),
        (403, {"detail": "duplicate"}, "duplicate"),
        (403, {"detail": "suspended"}, "suspended"),
        (403, {"detail": "denied"}, "Forbidden"),
        (429, {}, "Rate limit"),
        (400, {"errors": [{"message": "invalid fixture"}]}, "invalid fixture"),
        (400, {}, "invalid parameters"),
        (500, {"detail": "offline"}, "offline"),
    ],
)
async def test_post_provider_errors(
    api: twitter.XTwitterAPI,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    payload: dict[str, Any],
    expected: str,
) -> None:
    transport(monkeypatch, status, payload)
    result = await api.post_tweet("fixture")
    assert result["success"] is False
    assert result["status_code"] == status
    assert expected in result["message"]


@pytest.mark.asyncio
async def test_plain_error_and_invalid_success_json(
    api: twitter.XTwitterAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    transport(monkeypatch, 503, {}, "offline")
    assert (await api.post_tweet("fixture"))["error"] == {"detail": "offline"}
    transport(monkeypatch, 201, {}, "not JSON")
    with pytest.raises(MCPToolError, match="Failed to post"):
        await api.post_tweet("fixture")


@pytest.mark.asyncio
@pytest.mark.parametrize("text", ["", "   ", "x" * 281])
async def test_invalid_posts_do_not_open_transport(
    api: twitter.XTwitterAPI, monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    factory = Mock()
    monkeypatch.setattr(twitter.aiohttp, "ClientSession", factory)
    with pytest.raises(MCPToolError):
        await api.post_tweet(text)
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_user_lookup_and_verification(
    api: twitter.XTwitterAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(twitter, "x_api", api)
    session = transport(monkeypatch, 200, {"data": {"id": "fixture-user"}})
    assert (await twitter.verify_x_credentials_tool({}))["user"]["id"] == "fixture-user"
    assert (await twitter.get_x_user_info_tool({"username": "fixture"}))[
        "success"
    ] is True
    assert session.get.call_args.args[0].endswith("/users/by/username/fixture")
    await api.get_user_info()
    assert session.get.call_args.args[0].endswith("/users/me")
    transport(monkeypatch, 401, {"detail": "denied"})
    api.oauth1a_available = True
    assert (await api.verify_credentials())["success"] is False
    assert (await api.get_user_info())["status_code"] == 401
    api.bearer_token = None
    assert (await api.verify_credentials())["success"] is False
    assert (await api.get_user_info())["success"] is False
    with pytest.raises(MCPToolError, match="OAuth 1.0a available"):
        api._get_auth_headers()
    with pytest.raises(MCPToolError, match="Text parameter"):
        await twitter.post_tweet_tool({})


@pytest.mark.asyncio
async def test_token_fallback_precedence(
    api: twitter.XTwitterAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("X_OAUTH2_ACCESS_TOKEN", "fallback-fixture")
    assert api._get_bearer_token() == "fixture-only"
    monkeypatch.delenv("X_BEARER_TOKEN")
    assert api._get_bearer_token() == "fallback-fixture"
    monkeypatch.delenv("X_OAUTH2_ACCESS_TOKEN")
    assert api._get_bearer_token() is None
