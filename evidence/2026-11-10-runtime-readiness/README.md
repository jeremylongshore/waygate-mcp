# Runtime readiness verification — 2026-11-10

Tracked by bd_000-projects-u8kx.49, stacked on dependency/security PR8.

Three regression-first checks failed before the repair: disabled providers were
attempted, the abstract bridge was discovered, and an enabled missing provider
was reported active. Six new regressions now cover those cases plus real SQLite
failure, configured-before-start provider failure, and observed disconnection or
process exit without a readiness-triggered restart.

The full source suite passes 239 tests on Python 3.11 and 3.12, with 81.94% and 81.97% respectively
branch coverage against the unchanged 80% floor. Configured formatting, lint
and mypy checks pass. Security failure contracts: 20 pass. Release/report
contracts: 26 pass. Bandit medium-floor and Semgrep scans report zero findings
and zero analysis errors. No scanner policy or measurement input was removed.

Image `sha256:112dbca8eef34ef27a49df8c190e54d7191e02a8ed89d3d20ab56db9023cb4cd`
was built from the repaired application. Disposable Compose validation proves:

- HTTP tool catalog, file roundtrip and path/tool refusals pass.
- SQLite contains five configuration records; the process is non-root and its
  private scratch directory has the expected owner and mode 0700.
- Empty provider enablement starts no Firebase/abstract bridge and reports
  local-only readiness with providers disabled.
- Dropping the actual SQLite configuration table makes both health endpoints
  return HTTP 503 with database failed.
- An enabled missing provider returns readiness 503 and integration degraded.
- Owned containers, volumes and networks are removed after each scenario.

The initial missing-provider smoke observed a startup connection reset; its
bounded retry handles that transient alongside connection refusal. A second probe used the legacy `/mcp/status` endpoint; the integration-state
assertion was corrected to `/mcp/servers`. These test corrections did not
change application behavior or accept a successful readiness response.

Provider readiness observes startup, last connection state and process exit;
it is not an active upstream availability probe. Database checks execute a real
query. No fixed cache/filesystem success claims remain in the health response.
Raw local evidence: `/tmp/iep-waygate-readiness-*` and
`/tmp/iep-waygate-required-provider-smoke-final.log`.

Integration is not complete: hosted checks and guarded merge remain required,
and the parent security PR still fails on retained/proxy dependency manifests
and historical credentials. No live cloud writes or history rewrite occurred.
