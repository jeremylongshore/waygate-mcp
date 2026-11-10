"""Real SQLite regression tests for the async fallback and its public helpers."""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from source.database import DatabaseManager


@pytest_asyncio.fixture
async def store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[tuple[ModuleType, DatabaseManager]]:
    # Never inherit a developer's or production database URL.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    module = importlib.import_module("source.database")
    manager = module.DatabaseManager()
    monkeypatch.setattr(module, "db_manager", manager)
    await manager.initialize()
    try:
        yield module, manager
    finally:
        await manager.config.engine.dispose()


@pytest.mark.asyncio
async def test_documented_sqlite_url_initializes_and_seeds_once(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    _, manager = store
    assert manager.config.database_url.startswith("sqlite+aiosqlite:///")
    health = await manager.get_health_status()
    assert health["database"] == "healthy"
    assert health["config_entries"] == 5
    await manager.config._create_tables()
    assert (await manager.get_health_status())["config_entries"] == 5


@pytest.mark.asyncio
async def test_named_positional_and_empty_bindings(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    _, manager = store
    value = "apostrophe'; DROP TABLE config; --"
    assert await manager.execute_query("SELECT ? AS value", [value]) == [
        {"value": value}
    ]
    assert await manager.execute_query("SELECT :value AS value", {"value": value}) == [
        {"value": value}
    ]
    assert await manager.execute_query("SELECT 7 AS value", []) == [{"value": 7}]
    assert await manager.execute_query("SELECT 8 AS value") == [{"value": 8}]
    assert (await manager.get_health_status())["config_entries"] == 5


@pytest.mark.asyncio
async def test_write_commits_and_bad_statement_does_not_poison_connection(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    _, manager = store
    assert (
        await manager.execute_query(
            "INSERT INTO config (key, value, type) VALUES (?, ?, ?)",
            ["sample", "value", "string"],
        )
        == []
    )
    with pytest.raises(Exception, match="UNIQUE constraint failed"):
        await manager.execute_query(
            "INSERT INTO config (key, value, type) VALUES (?, ?, ?)",
            ["sample", "replacement", "string"],
        )
    assert await manager.execute_query(
        "SELECT value FROM config WHERE key = :key", {"key": "sample"}
    ) == [{"value": "value"}]


@pytest.mark.asyncio
async def test_server_lifecycle_preserves_json_and_mixed_positional_values(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    module, manager = store
    assert await module.register_mcp_server(
        "fixture",
        "github",
        "Fixture",
        config={"nested": [1, 2]},
        credentials={"fixture": "not-a-real-credential"},
    )
    row = await module.get_mcp_server("fixture")
    assert row["config"] == {"nested": [1, 2]}
    assert row["credentials"] == {"fixture": "not-a-real-credential"}
    assert await module.update_mcp_server_status("fixture", "active", tool_count=3)
    active = await module.list_mcp_servers("active")
    assert len(active) == 1
    assert active[0]["tool_count"] == 3
    assert active[0]["last_sync"] is not None
    assert await module.update_mcp_server_status("fixture", "error", "failed", 0)
    row = await module.get_mcp_server("fixture")
    assert row["error_count"] == 1
    assert row["tool_count"] == 0
    assert await module.list_mcp_servers("active") == []
    assert len(await module.list_mcp_servers()) == 1
    assert await module.delete_mcp_server("fixture")
    assert await module.get_mcp_server("fixture") is None
    assert await module.list_mcp_servers() == []
    assert (await manager.get_health_status())["database"] == "healthy"


@pytest.mark.asyncio
async def test_command_audit_metric_and_event_persistence(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    module, manager = store
    await manager.log_command("command-1", "read", {"path": "fixture"})
    await manager.update_command_status(
        "command-1", "success", {"ok": True}, duration_ms=12
    )
    rows = await manager.execute_query("SELECT * FROM command_history")
    assert rows[0]["status"] == "success"
    assert rows[0]["duration_ms"] == 12
    assert rows[0]["result"] == '{"ok": true}'
    assert rows[0]["completed_at"] is not None
    await manager.record_metric("latency", 1.5, tags={"route": "fixture"})
    rows = await manager.execute_query("SELECT * FROM metrics")
    assert rows[0]["metric_value"] == 1.5
    await module.log_system_event("test", "fixture", context={"ok": True})
    rows = await manager.execute_query("SELECT * FROM system_events")
    assert rows[0]["context"] == '{"ok": true}'


@pytest.mark.asyncio
async def test_context_manager_propagates_failure(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    module, manager = store
    with pytest.raises(ValueError, match="caller failure"):
        async with module.get_db() as active:
            assert active is manager
            raise ValueError("caller failure")


@pytest.mark.asyncio
async def test_default_server_registration(
    store: tuple[ModuleType, DatabaseManager],
) -> None:
    module, _ = store
    await module.initialize_default_mcp_servers()
    servers = await module.list_mcp_servers()
    assert len(servers) == 6
    assert {row["server_type"] for row in servers} == {
        "firebase",
        "bigquery",
        "github",
        "n8n",
        "docker_hub",
        "slack",
    }


def test_connection_access_before_initialization_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    module = importlib.import_module("source.database")
    config = module.DatabaseConfig()
    for attribute in ("engine", "session_maker", "client"):
        with pytest.raises(RuntimeError, match="has not been initialized"):
            getattr(config, attribute)
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(ValueError, match="DATABASE_URL is required"):
        module.DatabaseConfig()


@pytest.mark.asyncio
async def test_libsql_client_local_file_uses_the_same_binding_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The libsql client's local-file transport exercises its API without a
    # remote Turso account, credentials or network access.
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    module = importlib.import_module("source.database")
    manager = module.DatabaseManager()
    manager.config.database_url = f"file:{tmp_path / 'libsql.db'}"
    manager.config.is_turso = True
    monkeypatch.setattr(module, "db_manager", manager)
    await manager.initialize()
    try:
        assert await manager.execute_query(
            "SELECT :second AS a, :first AS b", {"first": "first", "second": "second"}
        ) == [{"a": "second", "b": "first"}]
        assert await manager.execute_query("SELECT ? AS value", [3]) == [{"value": 3}]
        assert (await manager.get_health_status())["config_entries"] == 5
        assert await module.register_mcp_server("fixture", "github", "Fixture")
        assert await module.update_mcp_server_status("fixture", "active", tool_count=2)
        assert (await module.get_mcp_server("fixture"))["tool_count"] == 2
        await manager.log_command("libsql-1", "read")
        await manager.update_command_status("libsql-1", "failed", error="fixture")
        await manager.record_metric("counter", 2, "counter")
        await module.log_system_event("test", "fixture")
        assert await manager.execute_query(
            "SELECT status FROM command_history WHERE command_id = ?", ["libsql-1"]
        ) == [{"status": "failed"}]
        assert await module.delete_mcp_server("fixture")
        assert await module.list_mcp_servers() == []
    finally:
        manager.config.client.close()
