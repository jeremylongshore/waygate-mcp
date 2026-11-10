# Dependency profile verification — 2026-11-10

Four complete, hash-bearing profiles now support the documented root install,
standard server, container and development environment. The clean root install
previously failed with `ModuleNotFoundError: structlog`; fresh Python 3.11 and
3.12 installations now pass dependency checks and load the server CLI.

`bash ci/dependencies/compile.sh` reproduces all four profiles byte-for-byte.
Fresh development installations pass 233 source tests on both Python versions,
with 81.55% branch coverage against the unchanged 80% floor. Configured formatting,
lint and mypy checks pass, as do 20 security contracts, 26 release/report contracts
and two real benchmarks. The wheel loads outside the checkout; its source archive
contains the dynamic dependency inputs and the wheel excludes source tests.

Each profile passed the unchanged OSV 2.5.1 `scan source --lockfile=<profile>`
command, with no suppressions. Root extraction recognized 129 package records;
its actual Linux installations each contain 120 packages before installing the
project wheel. These counts differ because the lock includes universal markers.

The rebuilt image in receipt.json passed the pinned Trivy CRITICAL and secret
scan. A disposable Compose deployment exercised HTTP tool catalog, file roundtrip,
forbidden paths and unknown tools; SQLite contained five configuration records.
The process was non-root, its scratch directory was owned with mode 0700, and no
shared temporary log existed. All owned Compose resources were removed. The first
SQLite probe used an incorrect table name; the corrected `config` query passed.
This is not external-provider readiness evidence (tracked separately in u8kx.49).

The repository-wide fail-closed scan still includes all 14 inputs and FAILS:
733 dependency finding records, 406 blocking records, and 13 historical secret
findings. Records are not unique vulnerabilities. Proxy and retained manifests
remain unchanged and scanned; u8kx.52 tracks the missing proxy implementation.
No credential expiry or rotation is established by this receipt.

Package extras retain the prior security-tool lower bounds for compatibility;
they are not validated deployment locks. A combined dev/security metadata resolve
selects Semgrep 1.79.0 because current Semgrep 1.178.0 pins MCP 1.29.0 while the
application uses MCP 1.30.0. CI continues to run its pinned current scanners in
separate environments. Do not substitute the package extra for CI scanner setup.

Raw local evidence is under `/tmp/iep-waygate-locked-*`, including full-security,
image inventory, build, Trivy and smoke reports. The compact receipt records
profile hashes and bounded outcomes; it does not claim a clean repository.
