"""Run security measurements without converting unmeasured gates into passes."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

REQUIRED_INPUTS = (
    "source/requirements.txt",
    "source/requirements-docker.txt",
    "source/requirements-proxy.txt",
    "source/requirements-dev.txt",
    "requirements.txt",
    ".semgrep.yml",
)
REQUIRED_GATES = {
    "audit-harness:ci:cve-osv",
    "audit-harness:ci:sast",
    "audit-harness:ci:secrets-gitleaks",
    "audit-harness:ci:sbom-syft",
}


def execute(command, root):
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=900,
            env={**os.environ, "SEMGREP_RULES": str(root / ".semgrep.yml")},
        )
        return result.returncode, json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        # Tool output may contain credentials; never echo stdout/stderr on errors.
        return None, None


def scan(root, output):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError("security evidence must be outside the audited repository")
    output.mkdir(parents=True, exist_ok=False)
    missing = [name for name in REQUIRED_INPUTS if not (root / name).is_file()]
    if not (root / "source").is_dir():
        missing.append("source/")
    if missing:
        (output / "preflight.json").write_text(json.dumps({"missing_inputs": missing}))
        return 1

    (output / "preflight.json").write_text(
        json.dumps(
            {
                "input_sha256": {
                    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                    for name in REQUIRED_INPUTS
                },
                "semgrep_rules": ".semgrep.yml",
            },
            indent=2,
        )
        + "\n"
    )

    code, rows = execute(
        [
            "audit-harness",
            "scan",
            "--fail-closed",
            "--osv-severity-threshold",
            "HIGH",
            "--sbom-output",
            str(output / "sbom.json"),
            ".",
        ],
        root,
    )
    measured = isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
    if measured:
        (output / "gate-results.json").write_text(json.dumps(rows, indent=2) + "\n")
    required = {row.get("gate_id"): row for row in rows} if measured else {}
    valid = code == 0 and REQUIRED_GATES <= required.keys()
    for name in REQUIRED_GATES:
        row = required.get(name, {})
        allowed = {"PASS", "ADVISORY"} if name.endswith("cve-osv") else {"PASS"}
        valid = valid and row.get("result") in allowed
        valid = valid and not row.get("metadata", {}).get("indeterminate", False)
    valid = valid and (output / "sbom.json").is_file()

    bandit_code, report = execute(
        [
            "bandit",
            "-r",
            "source",
            "-f",
            "json",
            "--severity-level",
            "medium",
            "--confidence-level",
            "medium",
        ],
        root,
    )
    bandit_measured = (
        isinstance(report, dict)
        and isinstance(report.get("results"), list)
        and isinstance(report.get("errors"), list)
        and isinstance(report.get("metrics"), dict)
        and report["metrics"].get("_totals", {}).get("loc", 0) > 0
    )
    bandit_clean = (
        bandit_measured
        and bandit_code == 0
        and not report["results"]
        and not report["errors"]
    )
    # Preserve locations and rule IDs, never matched source or issue messages.
    summary = {
        "exit_code": bandit_code,
        "measured": bandit_measured,
        "clean": bandit_clean,
    }
    if bandit_measured:
        summary["findings"] = [
            {
                key: row.get(key)
                for key in (
                    "filename",
                    "line_number",
                    "test_id",
                    "issue_severity",
                    "issue_confidence",
                )
            }
            for row in report["results"]
            if isinstance(row, dict)
        ]
        summary["analysis_errors"] = len(report["errors"])
    (output / "bandit.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if valid and bandit_clean else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(scan(args.root, args.output))
