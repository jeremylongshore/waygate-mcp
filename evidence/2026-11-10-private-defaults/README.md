# Private runtime defaults — 2026-11-10

Refs bead bd_000-projects-wcze.12. Partial remediation; the full bead remains open.

Ten regression cases fail on the prior implementation and pass after the change:
private isolated scratch roots; configured scratch creation/reuse; refusal of
public, symlinked, relative or wrong-owner roots; loopback CLI/settings defaults
with explicit bind support; and no predictable file opened for logging.
The main server now logs to stderr. Unspecified-interface warnings use IP address
classification and cover IPv6 as well as IPv4.

Both Python 3.11 and 3.12 pass 210 tests at 81.51% branch coverage (unchanged 80%
floor). Configured mypy passes 33 files on both versions; Black/isort/flake8 pass.
Bandit 1.9.4 at medium severity/confidence and Semgrep 1.178.0 with the repository
rules both exit 0 with zero findings and zero analysis errors. Their JSON reports
are retained; no scanner rules or severity thresholds were relaxed.

Built image `waygate-mcp:iep-private-defaults`:
`sha256:493f31b197f77ce766173aa85fb7fed117781f93126680335534bfb3559e4dc6`.
Disposable Compose passed real SQLite seed assertions, HTTP catalog/file roundtrip,
disallowed/shared-temp path refusals and unknown-tool refusal. The container's
scratch root was owned by its non-root user with mode 0700; the old predictable log
file was absent. Containers and volumes were removed after the smoke test.
No live provider operation was performed. Health/provider-readiness defects remain
separately tracked; a successful HTTP response is not readiness proof.

Dependency inputs and historical credential evidence remain outstanding. These
source scanner results do not imply the complete repository security gate passes.
