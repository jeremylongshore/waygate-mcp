"""Local persistence and plugin-template behavior with disposable paths."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from source.database_simple import SimpleDatabaseManager
from source.example_tools import ExampleTools
from source.plugins.github_plugin import GitHubPlugin


@pytest.mark.asyncio
async def test_simple_database_health_and_event_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'simple.db'}")
    db = SimpleDatabaseManager()
    assert (await db.get_health_status())["database"] == "unhealthy"
    await db.initialize()
    await db.initialize()
    assert (await db.get_health_status())["config_entries"] == 1
    db.record_event("fixture")
    with sqlite3.connect(db.db_path) as connection:
        assert connection.execute(
            "SELECT event_type, description FROM events"
        ).fetchall() == [("fixture", None)]


@pytest.mark.asyncio
async def test_simple_database_failure_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'absent' / 'test.db'}")
    db = SimpleDatabaseManager()
    with pytest.raises(sqlite3.OperationalError):
        await db.initialize()
    assert (await db.get_health_status())["database"] == "unhealthy"
    db.record_event("fixture")  # Best-effort event recording must not mask its caller.
    monkeypatch.setenv("DATABASE_URL", "unsupported")
    assert SimpleDatabaseManager().db_path == "./waygate.db"


@pytest.mark.asyncio
async def test_note_todo_and_reminder_persist_across_instances(tmp_path: Path) -> None:
    tools = ExampleTools(str(tmp_path))
    result = await tools.save_note("Meeting", "Discuss release")
    notes = list(tmp_path.glob("note_*.json"))
    assert len(notes) == 1
    note = json.loads(notes[0].read_text())
    assert note["id"] == result["note_id"]
    assert note["tags"] == []
    await tools.add_todo("first")
    await tools.set_reminder("first", "2027-01-01")
    second = ExampleTools(str(tmp_path))
    assert (await second.add_todo("second", "high"))["todo_id"] == 2
    assert (await second.set_reminder("second", "2027-02-01"))["reminder_id"] == 2
    assert [
        item["task"] for item in json.loads((tmp_path / "todos.json").read_text())
    ] == ["first", "second"]
    assert len(json.loads((tmp_path / "reminders.json").read_text())) == 2


@pytest.mark.asyncio
async def test_example_calculator_refuses_code_and_reports_bad_arithmetic(
    tmp_path: Path,
) -> None:
    tools = ExampleTools(str(tmp_path))
    assert (await tools.calculate("2 + 3 * 4"))["result"] == 14
    assert (await tools.calculate("1 / 0"))["success"] is False
    assert (await tools.calculate("__import__('os')"))["success"] is False
    assert (await tools.lookup_info("OFFICE"))["success"] is True
    assert (await tools.lookup_info("not present"))["success"] is False
    assert (await tools.my_custom_tool("sample"))[
        "result"
    ] == "Processing sample with option default"


@pytest.mark.asyncio
async def test_github_plugin_generates_local_artifacts_without_api_calls(
    tmp_path: Path,
) -> None:
    plugin = GitHubPlugin(str(tmp_path))
    assert len(await plugin.get_tools()) == 4
    assert (await plugin.execute("unknown", {}))["success"] is False
    repo = await plugin.execute(
        "create_github_repo", {"repo_name": "fixture", "private": True}
    )
    assert repo["data"]["repository"]["private"] is True
    assert "template" in repo["message"]
    issue = await plugin.execute("create_issue", {"title": "Fixture", "body": "Body"})
    assert "## Fixture" in issue["data"]["markdown"]
    assert (await plugin.execute("list_my_repos", {}))["total"] == 3
    result = await plugin.execute(
        "create_readme", {"project_name": "Fixture", "author": "Test User"}
    )
    content = (tmp_path / "README_template.md").read_text()
    assert content == result["content"]
    assert "https://github.com/testuser" in content
    assert plugin.get_info()["name"] == "GitHub Integration"


@pytest.mark.asyncio
async def test_simple_server_reads_disposable_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from source import waygate_simple

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'server.db'}")
    db = SimpleDatabaseManager()
    monkeypatch.setattr(waygate_simple, "simple_db", db)
    await db.initialize()
    with TestClient(waygate_simple.create_app()) as client:
        for path in [
            "/",
            "/health",
            "/ready",
            "/metrics",
            "/mcp/status",
            "/proxy/health",
        ]:
            assert client.get(path).status_code == 200
        response = client.post("/mcp/execute", json={"action": "fixture"})
        assert response.json()["action"] == "fixture"
    with sqlite3.connect(db.db_path) as connection:
        assert connection.execute("SELECT event_type FROM events").fetchall() == [
            ("mcp_command",)
        ]
