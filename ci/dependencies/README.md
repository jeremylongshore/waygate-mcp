# Python dependency profiles

The `.in` files declare direct dependencies. The corresponding `.txt` files
contain the complete resolved graph, exact versions, environment markers and
distribution hashes. Install a generated profile with hash verification:

```sh
python -m pip install --require-hashes -r requirements.txt
```

| Profile | Direct input | Generated install file |
| --- | --- | --- |
| Standard server and integrations | `source/requirements.in` | `source/requirements.txt` |
| Standard container | `source/requirements-docker.in` | `source/requirements-docker.txt` |
| Development tools plus standard server | standard input + `source/requirements-dev.in` | `source/requirements-dev.txt` |
| Documented root installation | `requirements.in` includes standard input + `requirements-extra.in` | `requirements.txt` |

The root profile preserves the legacy Flask, requests, JSON5 and analytics
packages while also providing the server's actual runtime imports. It no longer
depends on an existing developer environment to supply undeclared packages.
The other three profiles use the standard lock as constraints so shared runtime
packages cannot silently diverge between the tested development environment and
the documented installation. The container profile retains its smaller feature
set; it does not add all optional cloud integrations.

Regenerate with the recorded compiler, uv 0.9.8:

```sh
bash ci/dependencies/compile.sh
# Intentionally refresh transitive versions within the declared constraints:
bash ci/dependencies/compile.sh --upgrade
```

Review both input and generated changes. The normal command preserves existing
compatible resolutions. Universal markers describe the resolver's platform and
Python variants; actual execution validation is on Linux Python 3.11 and 3.12,
not a claim that every marked platform has been exercised.

Package metadata reads the same direct inputs through setuptools, including
the existing `dev` and `security` extras. A wheel's dependency metadata is not
a deployment lock; use the generated `.txt` profile for a hash-checked install.
The security extra is declared separately in `source/requirements-security.in`;
the CI scanner toolchain keeps its own version and binary-integrity controls.
Both package extras preserve the prior security-tool lower bounds. Their combined
resolver may select older compatible scanners; use the isolated CI scanner setup
for security validation, not the package extras.

Before accepting an update, install into fresh environments, check dependency
compatibility, exercise the server import/CLI and full application tests, run
the release/security/benchmark contracts, scan each generated profile, and
rebuild/smoke-test the container when its graph changes. Keep the existing
coverage, mutation and scanner policies intact.

Proxy and retained historical manifests are separate unresolved profiles.
They remain visible to the repository-wide scan. Clean results for these four
profiles do not establish a clean repository, credential history or proxy
deployment. The proxy implementation gap is tracked by `u8kx.52`.
