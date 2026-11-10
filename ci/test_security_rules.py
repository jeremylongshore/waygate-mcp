"""Exercise the repository rules with real Semgrep, without committing findings."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class SecurityRuleTests(unittest.TestCase):
    def test_sensitive_logging_rule_parses_and_finds_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "sample.py"
            fixture.write_text(
                'logging.info(f"Password: {password}")\n'
                'print(f"API Key: {api_key}")\n'
                'logger.debug("credential=%s", access_token)\n'
                'logger.debug("request=%s", request_id)\n'
            )
            result = subprocess.run(
                [
                    "semgrep",
                    "scan",
                    "--config",
                    str(Path(__file__).resolve().parents[1] / ".semgrep.yml"),
                    "--json",
                    "--quiet",
                    "--error",
                    "--metrics=off",
                    "--disable-version-check",
                    "--no-git-ignore",
                    str(fixture),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["errors"], [])
            matches = [
                row["start"]["line"]
                for row in report["results"]
                if row["check_id"].endswith("sensitive-data-logging")
            ]
            self.assertEqual(sorted(matches), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
