# Security measurements

The Security Audit job installs audit-harness 2.0.0 from the integrity-bearing
npm lockfile, Bandit 1.9.4 and Semgrep 1.178.0. The installer verifies pinned
SHA-256 digests for Gitleaks 8.30.1, Syft 1.57.1 and OSV Scanner 2.5.1.

Run the same entrypoint locally after installing those tools:

```sh
npm ci --ignore-scripts --prefix ci/security
bash ci/security/install-tools.sh /tmp/waygate-security-bin
export PATH="/tmp/waygate-security-bin:$PWD/ci/security/node_modules/.bin:$PATH"
python -m unittest discover -s ci -p 'test_security*.py' -v
python ci/security_scan.py --output /tmp/waygate-security-reports-new
```

The output directory must be new and outside the repository. The harness scans
all detected dependency inputs with its HIGH threshold, runs the repository's
Semgrep rules, scans Git history with redacted Gitleaks reports, and retains a
Syft SBOM. Bandit additionally scans `source/` at the existing medium severity
and confidence floors. Required inputs, required gate rows and the SBOM must be
present. Tool errors, incomplete measurements and findings fail the job. The
artifact step runs even after failure and refuses missing evidence.

The central OSV contract replaces the previously masked Safety and pip-audit
commands. The central Gitleaks contract replaces the detect-secrets command that
only generated a baseline without enforcing findings. Syft replaces the stale
CycloneDX command and captures package/license metadata for the repository,
rather than reporting licenses from the scanner environment. Semgrep remains
configured explicitly through `SEMGREP_RULES` by `.semgrep.yml`; Bandit remains an additional scanner. There are no
new exclusions, advisory waivers or vulnerability suppressions.

`ci/test_security_scan.py` exercises clean measurements, findings, exit/report
disagreement, missing gates/tools/inputs/SBOM, tool crashes, invalid reports,
timeouts, incomplete analysis and stale evidence refusal. The released harness
owns each scanner's report validation; its contract is documented in the pinned
package's `docs/security-scanners.md` and `docs/dependency-scanning.md`.

This wiring does not establish that the current repository is clean. Legacy
manifests, source findings and historical credential evidence remain tracked in
bd_000-projects-wcze.12. Do not restore `|| true`, exclude old manifests merely to
turn CI green, or call a successful scan proof that a historical token was revoked.
