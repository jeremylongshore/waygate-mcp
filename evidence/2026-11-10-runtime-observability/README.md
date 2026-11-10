# Runtime observability and administration — 2026-11-10

Tracked by bd_000-projects-u8kx.53. This change is based on readiness PR17 and
security/dependency PR8; their outstanding integration blockers still apply.

Three regression tests fail against the prior code: HTTP metrics remain zero,
a loaded plugin is missing from the registry response, and reload cleanup never
runs while the endpoint reports success. Seven tests now cover those cases plus
catalog failure visibility, MCP reference replacement and failed reconnection,
disabled-provider unloading, unhandled HTTP errors and isolated server registries.

Full source suites: 246 tests pass on Python 3.11 and 3.12 at the unchanged 80%
branch coverage floor. Formatting, lint and configured mypy checks pass (38 files).
Twenty security failure contracts and 26 release/report contracts pass. Bandit
and Semgrep each report zero findings and analysis errors. Security policies and
scanner inputs are unchanged; no full-repository security-green claim is made.

Image `sha256:de3857d90479aa5fef78a64b0566d1b9af203052658c19ae63ad7b32fed22b2e`
passes disposable Compose validation of actual plugin listing and reload count,
local command catalog, nonzero HTTP request/error/duration measurements, tool
roundtrip/refusals, SQLite state, non-root/private scratch, local-only readiness,
and actual database-table failure returning 503. Owned containers, networks and
volumes were removed. Raw evidence: `/tmp/iep-waygate-observability-*`.

Metrics are per-process and exclude scrapes; HTTP errors mean status >=400 or
unhandled request failure, not tool errors carried in successful HTTP responses.
Reloads are serialized and replace MCP references, but are not transactional
rollback and may interrupt an in-flight plugin request. Disabled providers are
unloaded; cleanup/reload/reconnection failures remain explicit HTTP503 results.

Exact-head hosted checks and guarded integration remain required. This receipt
does not settle the bead, the unimplemented proxy, or historical credentials.
