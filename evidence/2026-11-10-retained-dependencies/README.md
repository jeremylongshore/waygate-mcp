# Retained dependency reconciliation — 2026-11-10

The migration report `audit-reports/0003-CHORE-092925-FILE-MIGRATION-COMPLETE.md`
identifies `04-assets/configs/development/` as migrated configuration and
`source-backup-092925/` as a retained safety copy. Their standard, development
and container requirements had identical stale versions in both locations.

All six manifests now mirror the corresponding maintained, hash-bearing source
profiles. The regeneration script updates those copies after compiling the source
profiles. No manifest paths were removed or excluded. The proxy manifests remain
unchanged and separately unresolved.

Validation: original maintained-profile hashes are unchanged; all six copies
match their corresponding source lock byte-for-byte after regeneration;
ShellCheck passes; 68 retained-source security/calculator tests pass. The same
standard/development/container graphs already passed clean installs, source tests,
OSV and container validation in evidence/2026-11-10-dependency-profiles/.

The prior python-jose dependency has no imports in `source-backup-092925/` or
`02-src/`; these copies now follow its removal from maintained profiles. This
updates install dependencies, not the old service implementations or historical
release claims. The retained server entrypoints are not certified as deployable
by the focused tests or by a clean dependency scan.

The unchanged full repository scan still covers 14 inputs and fails: 463 dependency
finding records (262 blocking), all confined to the three `requirements-proxy.txt`
manifests. Counts are records, not unique vulnerabilities. Gitleaks reports 13
historical findings; SAST reports zero findings; Syft succeeds. Raw reports:
`/tmp/iep-waygate-retained-lock-full-security/`. Credential history and the
unimplemented proxy deployment remain unresolved; this is not a merge or closure
receipt.
