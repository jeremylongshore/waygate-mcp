"""Release failures must prevent the only remote mutation."""

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import publish

SHA = "a" * 40
OLD = "b" * 40


def good_run():
    return {
        "head_sha": SHA,
        "head_branch": "main",
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "path": ".github/workflows/ci.yml",
        "head_repository": {"full_name": publish.REPOSITORY},
    }


def good_jobs():
    return [
        {
            "name": name,
            "conclusion": "success",
            "steps": [
                {
                    "name": "Run fail-closed security measurements",
                    "conclusion": "success",
                }
            ],
        }
        for name in publish.REQUIRED_JOBS
    ]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source").mkdir()
        (self.root / "source/version.py").write_text('VERSION = "2.3.0"\n')
        (self.root / "version.txt").write_text("2.3.0\n")
        (self.root / "pyproject.toml").write_text('[project]\nversion = "2.3.0"\n')
        (self.root / "CHANGELOG.md").write_text("# Release v2.3.0\nReviewed changes\n")
        self.run = good_run()
        self.jobs = good_jobs()
        self.tags = {"v2.2.2": OLD}
        self.releases = []
        self.main = SHA
        self.writes = []
        self.fail_write = False
        self.api_patch = patch.object(publish, "api", side_effect=self.api)
        self.command_patch = patch.object(publish, "command", side_effect=self.command)
        self.tags_patch = patch.object(
            publish, "remote_tags", side_effect=lambda: dict(self.tags)
        )
        for mock in [self.api_patch, self.command_patch, self.tags_patch]:
            mock.start()
            self.addCleanup(mock.stop)

    def api(self, path):
        if path == "git/ref/heads/main":
            return {"object": {"sha": self.main}}
        if path == "actions/runs/42":
            return copy.deepcopy(self.run)
        if path.startswith("releases/tags/"):
            return {"draft": False, "prerelease": False}
        raise AssertionError(path)

    def command(self, *args):
        if args == ("git", "rev-parse", "HEAD"):
            return SHA
        if args == ("git", "status", "--porcelain"):
            return ""
        if args[:3] == ("git", "merge-base", "--is-ancestor"):
            return ""
        if args[:2] == ("gh", "api"):
            if "/jobs?" in args[-1]:
                return json.dumps([{"jobs": self.jobs}])
            if "/releases?" in args[-1]:
                return json.dumps([self.releases])
        if args[:3] == ("gh", "release", "create"):
            self.writes.append(args)
            if self.fail_write:
                raise subprocess.CalledProcessError(1, args)
            self.tags[args[3]] = SHA
            return "https://example.invalid/release"
        raise AssertionError(args)

    def test_validated_success_publishes_exact_sha_once(self):
        receipt = publish.publish(self.root, 42, True)
        self.assertTrue(receipt["published"])
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.writes[0][self.writes[0].index("--target") + 1], SHA)

    def test_dry_run_never_writes(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        receipt = publish.publish(self.root, 42)
        self.assertTrue(receipt["dry_run"])
        self.assertEqual(self.writes, [])
        self.assertEqual(
            before,
            {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()},
        )

    def test_failed_missing_stale_or_untrusted_ci_never_publishes(self):
        for key, value in [
            ("head_sha", OLD),
            ("head_branch", "feature"),
            ("event", "pull_request"),
            ("status", "in_progress"),
            ("conclusion", "failure"),
            ("path", ".github/workflows/fake.yml"),
            ("head_repository", {}),
        ]:
            with self.subTest(key=key):
                self.run = good_run()
                self.run[key] = value
                with self.assertRaises(ValueError):
                    publish.publish(self.root, 42, True)
                self.assertEqual(self.writes, [])

    def test_every_required_job_must_succeed(self):
        for name in publish.REQUIRED_JOBS:
            for conclusion in ["failure", "skipped", "cancelled", None]:
                with self.subTest(name=name, conclusion=conclusion):
                    self.jobs = good_jobs()
                    next(j for j in self.jobs if j["name"] == name)[
                        "conclusion"
                    ] = conclusion
                    with self.assertRaises(ValueError):
                        publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_missing_and_duplicate_job_fail(self):
        for jobs in [good_jobs()[1:], good_jobs() + [good_jobs()[0]]]:
            self.jobs = jobs
            with self.assertRaises(ValueError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_masked_legacy_security_does_not_qualify(self):
        next(j for j in self.jobs if j["name"] == "🔒 Security Audit")["steps"] = []
        with self.assertRaises(ValueError):
            publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_stale_main_fails(self):
        self.main = OLD
        with self.assertRaises(ValueError):
            publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_main_advance_during_validation_fails(self):
        original = self.api
        count = 0

        def advancing(path):
            nonlocal count
            if path == "git/ref/heads/main":
                count += 1
                if count > 1:
                    return {"object": {"sha": OLD}}
            return original(path)

        with patch.object(publish, "api", side_effect=advancing):
            with self.assertRaises(ValueError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_duplicate_publication_is_noop(self):
        self.tags["v2.3.0"] = SHA
        self.releases = [{"tag_name": "v2.3.0", "draft": False, "prerelease": False}]
        self.assertEqual(
            publish.publish(self.root, 42, True)["decision"], "already_published"
        )
        self.assertEqual(self.writes, [])

    def test_conflicting_release_is_refused(self):
        self.releases = [{"tag_name": "v2.3.0", "draft": False, "prerelease": False}]
        with self.assertRaises(ValueError):
            publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_existing_version_on_ancestor_is_not_retagged(self):
        self.tags["v2.3.0"] = OLD
        self.assertEqual(publish.publish(self.root, 42, True)["decision"], "unchanged")
        self.assertEqual(self.writes, [])

    def test_existing_nonancestor_tag_fails(self):
        self.tags["v2.3.0"] = OLD
        original = self.command

        def reject_ancestry(*args):
            if args[:3] == ("git", "merge-base", "--is-ancestor"):
                raise subprocess.CalledProcessError(1, args)
            return original(*args)

        with patch.object(publish, "command", side_effect=reject_ancestry):
            with self.assertRaises(subprocess.CalledProcessError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_publish_error_is_not_masked(self):
        self.fail_write = True
        with self.assertRaises(subprocess.CalledProcessError):
            publish.publish(self.root, 42, True)

    def test_api_failure_never_publishes(self):
        with patch.object(
            publish, "api", side_effect=subprocess.CalledProcessError(1, ["gh"])
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_tag_created_during_validation_stops_publication(self):
        with patch.object(
            publish,
            "remote_tags",
            side_effect=[self.tags, {**self.tags, "v2.3.0": OLD}],
        ):
            with self.assertRaises(ValueError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_ci_rerun_stops_publication(self):
        original = self.api
        count = 0

        def rerun(path):
            nonlocal count
            result = original(path)
            if path == "actions/runs/42":
                count += 1
                result["run_attempt"] = count
            return result

        with patch.object(publish, "api", side_effect=rerun):
            with self.assertRaises(ValueError):
                publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_partial_tag_creation_can_resume_at_same_sha(self):
        self.tags["v2.3.0"] = SHA
        self.assertTrue(publish.publish(self.root, 42, True)["published"])
        self.assertEqual(len(self.writes), 1)

    def test_remote_tag_parser_peels_annotated_tags(self):
        self.tags_patch.stop()
        output = f"{OLD}\trefs/tags/v2.2.2\n{SHA}\trefs/tags/v2.2.2^{{}}\n"
        with patch.object(publish, "command", return_value=output):
            self.assertEqual(publish.remote_tags(), {"v2.2.2": SHA})

    def test_mismatched_metadata_fails(self):
        (self.root / "source/version.py").write_text('VERSION = "2.0.0"\n')
        with self.assertRaises(ValueError):
            publish.publish(self.root, 42, True)
        self.assertEqual(self.writes, [])

    def test_changelog_required(self):
        (self.root / "CHANGELOG.md").write_text("old version")
        with self.assertRaises(ValueError):
            publish.read_version(self.root)

    def test_versions_must_be_stable_semver(self):
        for value in ["2.3", "v2.3.0", "2.03.0", "2.3.0-rc1", "-1.0.0", "2.3.0\n"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                publish.version_tuple(value)

    def test_version_rollback_fails(self):
        with self.assertRaises(ValueError):
            publish.decide("2.1.0", SHA, self.tags)


if __name__ == "__main__":
    unittest.main()
