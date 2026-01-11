#!/bin/bash
# Run tests for all packages in the workspace

for pkg in mg mg-core mg-cli; do
  echo -n "$pkg: "
  output=$(cd "$(dirname "$0")/$pkg" && uv run pytest -q --tb=no "$@" 2>&1)
  echo "$output" | grep -E "^[0-9]+ passed|^FAILED|^ERROR|failed|error" | tail -1
done
