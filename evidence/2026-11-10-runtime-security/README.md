# Waygate runtime dependency remediation — 2026-11-10

Refs bead bd_000-projects-wcze.12. This is partial remediation, not bead closure.

Fresh Python 3.11 and 3.12 runtime/test environments each passed 132 tests at
88.92% branch coverage (unchanged 80% floor). The configured mypy, Black,
isort and flake8 checks passed. The complete development requirements were
also installed under Python 3.11: 220 packages, compatible according to
`uv pip check`, all 132 tests passing and the same quality checks passing.

OSV Scanner 2.5.1 scanned the attached exact installed inventories with:

```sh
osv-scanner scan source --no-resolve --lockfile development-requirements.txt --format json
osv-scanner scan source --no-resolve --lockfile container-requirements.txt --format json
```

Both exited 0 with no reported vulnerabilities: 220 development packages and
78 container packages. `--no-resolve` prevents a second inferred dependency
graph; these inventories already enumerate every installed distribution.
No advisory suppressions, exclusions or severity thresholds were used.
Reports retain the original temporary input paths. These are dated inventories,
not installation lockfiles; future resolution and advisory changes need fresh scans.

Built image `waygate-mcp:iep-security`:
`sha256:fca6f79838194d2905a0d58e2ae460ac1f791d5d40cdc6867ee7075b65c9c862`.
A disposable Compose run passed actual SQLite state assertions, HTTP tool catalog,
file write/read, disallowed-path refusal and unknown-tool refusal. All owned
containers, network and volumes were removed. No live provider operations ran.
The existing disabled-provider and health/readiness defects remain tracked in
bd_000-projects-u8kx.49; the HTTP health response is not provider-readiness proof.

Still required for wcze.12: fail-closed security workflow and failure fixtures,
root/proxy/retained-manifest reconciliation, source/secret scans, historical
credential remediation evidence, hosted checks and guarded merge. The existing
workflow still masks scanner failures. This bundle does not claim otherwise.

## Inventory and report hashes

- `container-osv.json`: `54345d5194d238b6017d0f3181f392109ce35023cc6b4bdfa8c134943dcb578e`
- `container-requirements.txt`: `54ee9a76189a34aed721844d6527e5c9a9d36e469acd96dd36286ee609afa5c2`
- `development-osv.json`: `54345d5194d238b6017d0f3181f392109ce35023cc6b4bdfa8c134943dcb578e`
- `development-requirements.txt`: `2d2b77244dfbdc4a499fdc41ca15f0828e0ad5ceea31d3dff24497a186e40f91`

Pinned Trivy image `aquasec/trivy@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb` exited 0 with `image --exit-code 1 --severity CRITICAL` against the built image. No critical findings or detected secrets were reported; this is not an all-severity OS-package claim.

- `container-trivy-critical.json`: `927a508d277cbad035b1e005a0e13232774defc765f764eac1131abc47725c2b`
