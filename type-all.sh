#!/bin/bash
# Run type checking for all packages in the workspace

for pkg in haiv-lib haiv-core haiv-cli; do
  echo -n "$pkg: "
  output=$(cd "$(dirname "$0")/$pkg" && uv run ty check 2>&1)
  if [ $? -eq 0 ]; then
    echo "ok"
  else
    echo "errors"
    echo "$output"
  fi
done
