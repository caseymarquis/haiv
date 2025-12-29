#!/bin/bash
# Run tests for all packages in the workspace

for pkg in mg mg-core mg-cli; do
  echo "=== $pkg ==="
  (cd "$(dirname "$0")/$pkg" && uv run pytest -q "$@")
  echo
done
