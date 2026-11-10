"""Failure-path contracts for the CI security entrypoint."""

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "security_scan", Path(__file__).with_name("security_scan.py")
)
SCAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN)


class SecurityGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "repo"
        self.output = self.base / "evidence"
        self.binaries = self.base / "bin"
        self.binaries.mkdir()
        for name in SCAN.REQUIRED_INPUTS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n")
        self.rows = [
            {"gate_id": name, "result": "PASS", "metadata": {}}
            for name in SCAN.REQUIRED_GATES
        ]
        self.bandit = {"results": [], "errors": [], "metrics": {"_totals": {"loc": 1}}}

    def tool(self, name, report, code=0, raw=False):
        executable = self.binaries / name
        payload = report if raw else json.dumps(report)
        body = "#!/usr/bin/env python3\nimport os,pathlib,sys\n"
        if name == "audit-harness":
            body += (
                "assert os.environ['SEMGREP_RULES'] == "
                "str(pathlib.Path.cwd()/'.semgrep.yml')\n"
            )
            body += (
                "pathlib.Path(sys.argv[sys.argv.index('--sbom-output')+1])"
                ".write_text('{}')\n"
            )
        body += f"print({payload!r})\nsys.exit({code})\n"
        executable.write_text(body)
        executable.chmod(0o755)

    def run_gate(self, harness_code=0, bandit_code=0):
        self.tool("audit-harness", self.rows, harness_code)
        self.tool("bandit", self.bandit, bandit_code)
        with patch.dict(
            os.environ, {"PATH": str(self.binaries) + os.pathsep + os.environ["PATH"]}
        ):
            return SCAN.scan(self.root, self.output)

    def test_measured_clean_passes(self):
        self.assertEqual(self.run_gate(), 0)

    def test_ambient_rule_override_cannot_replace_repo_rules(self):
        with patch.dict(os.environ, {"SEMGREP_RULES": "fixture-wrong-rules"}):
            self.assertEqual(self.run_gate(), 0)

    def test_dependency_finding_fails(self):
        self.rows[0]["result"] = "FAIL"
        self.assertEqual(self.run_gate(harness_code=1), 1)

    def test_failed_row_cannot_be_masked_by_exit_zero(self):
        self.rows[0]["result"] = "FAIL"
        self.assertEqual(self.run_gate(), 1)

    def test_missing_required_gate_fails(self):
        self.rows.pop()
        self.assertEqual(self.run_gate(), 1)

    def test_unmeasured_gate_fails(self):
        self.rows[0]["metadata"]["indeterminate"] = True
        self.assertEqual(self.run_gate(), 1)

    def test_waived_required_gate_fails(self):
        self.rows[0]["result"] = "NOT_APPLICABLE"
        self.assertEqual(self.run_gate(), 1)

    def test_crash_with_clean_report_fails(self):
        self.assertEqual(self.run_gate(harness_code=2), 1)

    def test_bandit_finding_is_redacted_and_fails(self):
        self.bandit["results"] = [
            {
                "test_id": "B999",
                "code": "fixture-sensitive-value",
                "issue_text": "fixture-sensitive-value",
            }
        ]
        self.assertEqual(self.run_gate(bandit_code=1), 1)
        self.assertNotIn(
            "fixture-sensitive-value", (self.output / "bandit.json").read_text()
        )

    def test_bandit_analysis_error_fails(self):
        self.bandit["errors"] = [{"reason": "fixture parse error"}]
        self.assertEqual(self.run_gate(), 1)

    def test_bandit_scanning_zero_lines_fails(self):
        self.bandit["metrics"]["_totals"]["loc"] = 0
        self.assertEqual(self.run_gate(), 1)

    def test_bandit_crash_fails(self):
        self.assertEqual(self.run_gate(bandit_code=2), 1)

    def test_missing_input_does_not_run_scanners(self):
        (self.root / "source/requirements.txt").unlink()
        with patch.object(SCAN, "execute") as execute:
            self.assertEqual(SCAN.scan(self.root, self.output), 1)
            execute.assert_not_called()

    def test_missing_executable_is_unmeasured(self):
        self.assertEqual(
            SCAN.execute([str(self.base / "missing")], self.root), (None, None)
        )

    def test_malformed_report_is_unmeasured(self):
        self.tool("broken", "not JSON", raw=True)
        self.assertEqual(
            SCAN.execute([str(self.binaries / "broken")], self.root), (None, None)
        )

    def test_timeout_is_unmeasured(self):
        with patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 900)
        ):
            self.assertEqual(SCAN.execute(["fixture"], self.root), (None, None))

    def test_existing_evidence_cannot_supply_stale_sbom(self):
        self.output.mkdir()
        (self.output / "sbom.json").write_text("{}")
        with self.assertRaises(FileExistsError):
            SCAN.scan(self.root, self.output)

    def test_missing_sbom_fails(self):
        with patch.object(
            SCAN, "execute", side_effect=[(0, self.rows), (0, self.bandit)]
        ):
            self.assertEqual(SCAN.scan(self.root, self.output), 1)

    def test_evidence_inside_repository_refused(self):
        with self.assertRaises(ValueError):
            SCAN.scan(self.root, self.root / "reports")


if __name__ == "__main__":
    unittest.main()
