# Reviewed release versions

`release.yml` is the only publisher. It runs after successful main push CI,
checks the exact commit and required jobs again, and creates a GitHub release
targeting that commit. It does not publish an npm or PyPI package, edit files,
commit to main, or rewrite tags. The CI job named **Release Management** validates
this contract; it does not publish while CI is still running.

For a new release, open a normal PR that updates all three version declarations:
`version.txt`, `pyproject.toml` (`project.version`), and `source/version.py`.
Add a `# Release vMAJOR.MINOR.PATCH` entry to `CHANGELOG.md`, and update the
current-version references in the README. Choose the bump according to the
compatibility impact. The runtime uses `source.version.VERSION` for its API,
health response, and startup banner. CI rejects inconsistent version declarations.

After the PR passes review and merges, a successful push CI run can publish the
new version. A normal merge retaining an already released version is a no-op,
provided the existing tag is an ancestor and its stable release exists. A
version rollback, conflicting tag/release, missing job, skipped job, failed job,
stale main commit, API failure or publishing failure stops the operation.
An interrupted release with a tag at the exact validated commit can be retried;
an already published release at that commit is not recreated.

New publication also requires the successful **Run fail-closed security
measurements** step. The older masked Security Audit job is insufficient.
Until the security remediation lands and its real scans pass, new versions
cannot be published by this workflow. This is a deliberate dependency, not a
security exception. Existing-version no-ops perform no publication.

The manual Release workflow accepts a successful main push CI run ID and
defaults to **dry run**. Dry runs perform validation and reads but no tag,
release, branch, or version-file writes. Publication must target the current
main commit; a superseded candidate needs a new CI run. Workflow concurrency
serializes publishers, and main/tags are rechecked immediately before writing.
No workflow can atomically prevent a separately authorized actor from changing
Git refs; the published tag is checked against the validated SHA afterward.

Local contract tests require only Python 3.11 or later:

```sh
python -m unittest discover -s ci/release -p 'test_*.py' -v
python -c 'from pathlib import Path; from ci.release.publish import read_version; print(read_version(Path.cwd()))'
```

The publisher saves a JSON receipt with the candidate SHA, CI run ID, version,
decision and publication status. API and CLI errors propagate; no success
receipt is emitted for a failed operation.

GitHub documents the [workflow_run trust boundary](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run)
and [explicit release target behavior](https://cli.github.com/manual/gh_release_create).
