"""Private scratch storage and explicit network exposure defaults."""

import importlib
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from source.exceptions import MCPToolError
from source.mcp_tools import MCPToolsHandler


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("WAYGATE_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("WAYGATE_PROJECTS_DIR", str(tmp_path / "projects"))


def test_default_scratch_is_private_and_isolated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WAYGATE_SCRATCH_DIR", raising=False)
    first, second = MCPToolsHandler(str(tmp_path)), MCPToolsHandler(str(tmp_path))
    assert first.scratch_path != second.scratch_path
    assert stat.S_IMODE(first.scratch_path.stat().st_mode) == 0o700
    assert first._validate_path(str(first.scratch_path / "own.txt"))
    for other in [
        Path(tempfile.gettempdir()) / "unrelated.txt",
        second.scratch_path / "other.txt",
    ]:
        with pytest.raises(MCPToolError, match="Path not allowed"):
            first._validate_path(str(other))


def test_configured_scratch_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scratch = tmp_path / "scratch"
    monkeypatch.setenv("WAYGATE_SCRATCH_DIR", str(scratch))
    handler = MCPToolsHandler(str(tmp_path))
    assert handler.scratch_path == scratch
    assert stat.S_IMODE(scratch.stat().st_mode) == 0o700
    assert MCPToolsHandler(str(tmp_path)).scratch_path == scratch


@pytest.mark.parametrize("kind", ["public", "symlink", "relative", "wrong-owner"])
def test_unsafe_scratch_configuration_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir(mode=0o700)
    if kind == "public":
        scratch.chmod(0o777)
    elif kind == "symlink":
        link = tmp_path / "linked"
        link.symlink_to(scratch, target_is_directory=True)
        scratch = link
    elif kind == "wrong-owner":
        monkeypatch.setattr(os, "getuid", lambda: scratch.stat().st_uid + 1)
    monkeypatch.setenv(
        "WAYGATE_SCRATCH_DIR", "relative" if kind == "relative" else str(scratch)
    )
    with pytest.raises(ValueError):
        MCPToolsHandler(str(tmp_path))


@pytest.mark.parametrize("module_name", ["source.waygate_mcp", "source.waygate_simple"])
def test_cli_is_loopback_by_default_but_accepts_explicit_bind(
    module_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module(module_name)
    monkeypatch.delenv("WAYGATE_HOST", raising=False)
    host = next(
        parameter for parameter in module.main.params if parameter.name == "host"
    )
    assert host.default == "127.0.0.1"
    assert host.envvar == "WAYGATE_HOST"
    if module_name.endswith("waygate_mcp"):
        server = Mock()
        constructor = Mock(return_value=server)
        monkeypatch.setattr(module, "WaygateServer", constructor)
        monkeypatch.setattr(
            module, "signal", SimpleNamespace(signal=Mock(), SIGINT=2, SIGTERM=15)
        )
    else:
        monkeypatch.setattr(module.uvicorn, "run", Mock())
    result = CliRunner().invoke(module.main, ["--host", "192.0.2.1"])
    assert result.exit_code == 0
    if module_name.endswith("waygate_mcp"):
        assert constructor.call_args.args[0].host == "192.0.2.1"
    else:
        assert module.uvicorn.run.call_args.kwargs["host"] == "192.0.2.1"


def test_settings_default_to_loopback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("source.waygate_mcp")
    monkeypatch.delenv("WAYGATE_HOST", raising=False)
    settings = module.WaygateSettings(
        WAYGATE_DATA_DIR=tmp_path / "data", WAYGATE_PROJECTS_DIR=tmp_path / "projects"
    )
    assert settings.host == "127.0.0.1"


def test_import_never_opens_predictable_log_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from unittest.mock import patch; "
            "patch('logging.FileHandler', "
            "side_effect=AssertionError('unexpected file log')).start(); "
            "import source.waygate_mcp",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env={**os.environ, "WAYGATE_SCRATCH_DIR": str(tmp_path / "scratch")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
