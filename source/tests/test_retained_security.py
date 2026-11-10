"""Retained implementations must not silently hide unexpected failures."""

import importlib
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import NoReturn, cast

import pytest

from source import exceptions
from source.mcp_tools import MCPToolsHandler

RetainedHandler = tuple[ModuleType, MCPToolsHandler, Path]


@pytest.fixture(params=["02-src/features", "source-backup-092925"])
def retained(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[str]:
    name = "retained_security_fixture_" + uuid.uuid4().hex
    package = ModuleType(name)
    package.__path__ = [str(Path(__file__).resolve().parents[2] / request.param)]
    monkeypatch.setitem(sys.modules, name, package)
    # The retained feature fragment expects its host package to supply exceptions.
    monkeypatch.setitem(sys.modules, name + ".exceptions", exceptions)
    yield name
    for key in list(sys.modules):
        if key.startswith(name + "."):
            sys.modules.pop(key, None)


def test_unexpected_credential_validation_error_propagates(
    retained: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(retained + ".x_twitter_integration")
    auth = ModuleType(retained + ".x_oauth1a_auth")

    def fail() -> NoReturn:
        raise RuntimeError("fixture validation failed")

    setattr(auth, "validate_oauth1a_credentials", fail)
    monkeypatch.setitem(sys.modules, auth.__name__, auth)
    with pytest.raises(RuntimeError, match="fixture validation failed"):
        module.get_x_twitter_tools()


def test_missing_optional_auth_module_preserves_catalog(
    retained: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(retained + ".x_twitter_integration")
    monkeypatch.setitem(sys.modules, retained + ".x_oauth1a_auth", None)
    assert len(module.get_x_twitter_tools()) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [OSError, RuntimeError])
async def test_search_only_skips_expected_read_failures(
    retained: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    error: type[Exception],
) -> None:
    module = importlib.import_module(retained + ".mcp_tools")
    handler = module.MCPToolsHandler(str(tmp_path))
    handler.allowed_paths = [tmp_path]
    (tmp_path / "candidate.txt").write_text("needle")

    def fail(*args: object, **kwargs: object) -> NoReturn:
        raise error("fixture read failure")

    monkeypatch.setattr(Path, "read_text", fail)
    if error is OSError:
        assert (await handler.search_files({"path": str(tmp_path), "query": "needle"}))[
            "count"
        ] == 0
    else:
        with pytest.raises(module.MCPToolError, match="fixture read failure"):
            await handler.search_files({"path": str(tmp_path), "query": "needle"})


@pytest.fixture
def retained_handler(retained: str, tmp_path: Path) -> RetainedHandler:
    module = importlib.import_module(retained + ".mcp_tools")
    handler = module.MCPToolsHandler(str(tmp_path))
    root = tmp_path / "allowed"
    root.mkdir()
    handler.allowed_paths = [root]
    return module, cast(MCPToolsHandler, handler), root


@pytest.mark.asyncio
async def test_retained_file_roundtrip_search_and_listing(
    retained_handler: RetainedHandler,
) -> None:
    _, handler, root = retained_handler
    target = root / "nested" / "needle.txt"
    written = await handler.write_file({"path": str(target), "content": "needle café"})
    assert written["size"] == len("needle café".encode())
    read = await handler.read_file({"path": str(target)})
    assert read["content"] == "needle café"
    assert (await handler.list_directory({"path": str(root)}))["count"] == 1
    listing = await handler.list_directory(
        {"path": str(root), "recursive": True, "pattern": "*.txt"}
    )
    assert listing["entries"][0]["path"] == str(target)
    for mode in ["filename", "content", "both"]:
        result = await handler.search_files(
            {"path": str(root), "query": "needle", "type": mode}
        )
        assert result["count"] == 1
        assert result["results"][0]["path"] == str(target)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    ["read_file", "write_file", "list_directory", "search_files", "execute_command"],
)
async def test_retained_required_arguments(
    retained_handler: RetainedHandler, method: str
) -> None:
    module, handler, _ = retained_handler
    with pytest.raises(module.MCPToolError):
        await getattr(handler, method)({})


@pytest.mark.asyncio
async def test_retained_file_boundary_and_missing_paths(
    retained_handler: RetainedHandler,
) -> None:
    module, handler, root = retained_handler
    for method in [handler.read_file, handler.list_directory]:
        with pytest.raises(module.MCPToolError, match="does not exist"):
            await method({"path": str(root / "missing")})
        with pytest.raises(module.MCPToolError, match="Path not allowed"):
            await method({"path": str(root.parent / "outside")})
    with pytest.raises(module.MCPToolError, match="not a file"):
        await handler.read_file({"path": str(root)})
    file = root / "file.txt"
    file.write_text("fixture")
    with pytest.raises(module.MCPToolError, match="not a directory"):
        await handler.list_directory({"path": str(file)})
    with pytest.raises(module.MCPToolError, match="Content parameter"):
        await handler.write_file({"path": str(file)})
    with pytest.raises(module.MCPToolError, match="does not exist"):
        await handler.search_files({"path": str(root / "missing"), "query": "fixture"})


@pytest.mark.asyncio
async def test_retained_real_local_command_results(
    retained_handler: RetainedHandler,
) -> None:
    _, handler, _ = retained_handler
    result = await handler.execute_command({"command": "printf fixture"})
    assert result["stdout"] == "fixture"
    assert result["stderr"] == ""
    assert result["return_code"] == 0
    failed = await handler.execute_command({"command": "exit 7"})
    assert failed["return_code"] == 7
