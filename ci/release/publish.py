"""Publish a reviewed version from an exact, successful main CI run.

Only the final GitHub release creation mutates remote state. No branch commits,
version edits, force pushes, npm publishing, or failure-tolerant shell commands.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

REPOSITORY = "jeremylongshore/waygate-mcp"
REQUIRED_JOBS = {
    "🔒 Security Audit",
    "🧪 Test & Quality (3.11)",
    "🧪 Test & Quality (3.12)",
    "🐳 Docker Security",
    "🚀 Deployment Test",
    "⚡ Performance Benchmark",
    "📦 Release Management",
}
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def command(*args: str) -> str:
    return subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=120
    ).stdout.strip()


def api(endpoint: str) -> Any:
    return json.loads(command("gh", "api", f"repos/{REPOSITORY}/{endpoint}"))


def version_tuple(value: str) -> tuple[int, ...]:
    if not VERSION.fullmatch(value):
        raise ValueError("Release version must be stable MAJOR.MINOR.PATCH")
    return tuple(map(int, value.split(".")))


def read_version(root: Path) -> str:
    version = (root / "version.txt").read_text().strip()
    version_tuple(version)
    project = tomllib.loads((root / "pyproject.toml").read_text())
    runtime = (root / "source/version.py").read_text().strip()
    if project["project"]["version"] != version or runtime != f'VERSION = "{version}"':
        raise ValueError("version.txt, pyproject.toml and source/version.py must agree")
    if f"# Release v{version}" not in (root / "CHANGELOG.md").read_text():
        raise ValueError("Reviewed changelog entry is missing")
    return version


def validate_ci(run: dict[str, Any], jobs: list[dict[str, Any]], sha: str) -> None:
    expected = {
        "head_sha": sha,
        "head_branch": "main",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "path": ".github/workflows/ci.yml",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError("CI must be a successful push run for this exact main commit")
    if run.get("head_repository", {}).get("full_name") != REPOSITORY:
        raise ValueError("CI source repository does not match")
    for name in REQUIRED_JOBS:
        matches = [job for job in jobs if job.get("name") == name]
        if len(matches) != 1 or matches[0].get("conclusion") != "success":
            raise ValueError(f"Required CI job did not succeed: {name}")
    security = next(job for job in jobs if job["name"] == "🔒 Security Audit")
    if not any(
        step.get("name") == "Run fail-closed security measurements"
        and step.get("conclusion") == "success"
        for step in security.get("steps", [])
    ):
        raise ValueError("Release requires the fail-closed security measurement step")


def remote_tags() -> dict[str, str]:
    tags: dict[str, str] = {}
    lines = command("git", "ls-remote", "--tags", "origin").splitlines()
    for peeled in (False, True):
        for line in lines:
            sha, ref = line.split()
            if ref.endswith("^{}") != peeled:
                continue
            name = ref.removeprefix("refs/tags/").removesuffix("^{}")
            if name.startswith("v") and VERSION.fullmatch(name[1:]):
                tags[name] = sha
    return tags


def decide(version: str, sha: str, tags: dict[str, str]) -> str:
    """Unchanged released versions are normal; never retarget an existing tag."""
    latest = max((version_tuple(tag[1:]) for tag in tags), default=(0, 0, 0))
    if version_tuple(version) < latest:
        raise ValueError("Candidate version is behind the latest stable tag")
    existing = tags.get(f"v{version}")
    if existing == sha:
        return "resume"
    if existing:
        return "unchanged"
    return "new"


def publish(root: Path, run_id: int, write: bool = False) -> dict[str, Any]:
    version = read_version(root)
    sha = command("git", "rev-parse", "HEAD")
    if command("git", "status", "--porcelain"):
        raise ValueError("Release checkout must be clean")
    if api("git/ref/heads/main")["object"]["sha"] != sha:
        raise ValueError("Candidate is stale; main has advanced")
    tag = f"v{version}"
    tags = remote_tags()
    decision = decide(version, sha, tags)
    receipt: dict[str, Any] = {
        "version": version,
        "sha": sha,
        "ci_run_id": run_id,
        "decision": decision,
        "published": False,
        "dry_run": not write,
    }
    if decision == "unchanged":
        # A normal code merge does not implicitly choose a new release version.
        # Verify ancestry and an actual release before treating it as complete.
        command("git", "merge-base", "--is-ancestor", tags[tag], sha)
        release = api(f"releases/tags/{tag}")
        if release.get("draft") or release.get("prerelease"):
            raise ValueError("Existing version is not a published stable release")
        return receipt
    run = api(f"actions/runs/{run_id}")
    pages = json.loads(
        command(
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{REPOSITORY}/actions/runs/{run_id}/jobs?filter=latest&per_page=100",
        )
    )
    validate_ci(run, [job for page in pages for job in page["jobs"]], sha)
    releases = json.loads(
        command(
            "gh",
            "api",
            "--paginate",
            "--slurp",
            f"repos/{REPOSITORY}/releases?per_page=100",
        )
    )
    matches = [r for page in releases for r in page if r["tag_name"] == tag]
    if matches:
        if (
            decision != "resume"
            or len(matches) != 1
            or matches[0]["draft"]
            or matches[0]["prerelease"]
        ):
            raise ValueError("Conflicting release already exists")
        receipt["decision"] = "already_published"
        return receipt
    if not write:
        return receipt
    # Recheck both mutable boundaries immediately before the only remote write.
    if api("git/ref/heads/main")["object"]["sha"] != sha or remote_tags() != tags:
        raise ValueError("Main or release tags changed during validation")
    current_run = api(f"actions/runs/{run_id}")
    if current_run.get("run_attempt") != run.get("run_attempt"):
        raise ValueError("CI was rerun during release validation")
    validate_ci(
        current_run,
        [job for page in pages for job in page["jobs"]],
        sha,
    )
    command(
        "gh",
        "release",
        "create",
        tag,
        "--repo",
        REPOSITORY,
        "--target",
        sha,
        "--title",
        tag,
        "--generate-notes",
    )
    if remote_tags().get(tag) != sha:
        raise ValueError("Published tag does not resolve to the validated commit")
    release = api(f"releases/tags/{tag}")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Release was not published as stable")
    receipt["published"] = True
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    if args.run_id <= 0:
        parser.error("run-id must be positive")
    print(json.dumps(publish(Path.cwd(), args.run_id, args.publish), sort_keys=True))


if __name__ == "__main__":
    main()
