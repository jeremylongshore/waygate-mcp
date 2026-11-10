# Fail-closed security measurement — 2026-11-10

Refs bead bd_000-projects-wcze.12. The real security entrypoint exits 1.
OSV reported 993 finding records across 14 inputs, 538 above its blocking
policy. These include repeated manifests and inferred resolution; they are not
993 unique vulnerabilities in the tested runtime. Semgrep reported six findings
with no analysis error. Gitleaks reported 13 historical findings. Bandit reported
eight medium-or-higher findings with no analysis error. Syft produced a valid SBOM.

The 20 security entrypoint/rule tests pass on Python 3.11 and 3.12. The real
Semgrep rule fixture catches password, API-key and token logging and permits
request-ID logging. Actionlint, shell syntax, Black, isort, flake8 and diff checks
pass. No scanner findings were waived or converted to success.

The receipt retains sanitized gate outcomes and exact full-report hashes;
Bandit evidence omits source text and rule messages. Full local reports remain
at `/tmp/iep-waygate-failclosed-final-20261110/`. CI uploads the full sanitized
harness rows, SBOM, Bandit locations and input hashes on either success or failure.
The semgrep rules are explicitly selected and their input hash is retained.

Remaining findings require remediation before this draft is merge-ready.
Historical secret findings do not establish current validity or revocation.
The separate runtime inventory bundle covers its exact installed environments;
this broader source scan intentionally also covers root and retained manifests.
