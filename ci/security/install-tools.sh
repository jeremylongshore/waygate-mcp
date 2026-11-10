#!/usr/bin/env bash
# CI runner contract: Linux x86_64. Published archive digests are pinned below.
set -euo pipefail
[[ $# == 1 && $(uname -s) == Linux && $(uname -m) == x86_64 ]] || exit 2
destination=$1
mkdir -p "$destination"
destination=$(cd "$destination" && pwd)
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
install_tool() {
  local name=$1 url=$2 digest=$3
  curl --fail --location --silent --show-error --retry 3 "$url" -o "$temporary/$name.tar.gz"
  printf '%s  %s\n' "$digest" "$temporary/$name.tar.gz" | sha256sum --check --status
  tar -xzf "$temporary/$name.tar.gz" -C "$temporary" "$name"
  install -m 0755 "$temporary/$name" "$destination/$name"
}
install_tool gitleaks https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb
install_tool syft https://github.com/anchore/syft/releases/download/v1.57.1/syft_1.57.1_linux_amd64.tar.gz bf52519eb57f675d47c07d43213cb6dff6449f3d6d1147ff6701ed91f44eef0c
bash "$(dirname "$0")/node_modules/@intentsolutions/audit-harness/scripts/install-osv-scanner.sh" "$destination"
