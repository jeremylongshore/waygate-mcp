#!/usr/bin/env bash
# Regenerate complete, hash-checked Python dependency profiles.
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
if [[ "$(uv --version)" != 'uv 0.9.8' ]]; then
  echo 'Dependency regeneration requires uv 0.9.8.' >&2
  exit 1
fi
common=(--python-version 3.11 --universal --generate-hashes
  --custom-compile-command 'bash ci/dependencies/compile.sh')
if [[ "${1:-}" == '--upgrade' && $# == 1 ]]; then
  common+=(--upgrade)
elif [[ $# != 0 ]]; then
  echo 'Usage: bash ci/dependencies/compile.sh [--upgrade]' >&2
  exit 1
fi
uv pip compile "${common[@]}" source/requirements.in -o source/requirements.txt
uv pip compile "${common[@]}" -c source/requirements.txt source/requirements-docker.in -o source/requirements-docker.txt
uv pip compile "${common[@]}" -c source/requirements.txt source/requirements.in source/requirements-dev.in -o source/requirements-dev.txt
uv pip compile "${common[@]}" -c source/requirements.txt requirements.in -o requirements.txt
