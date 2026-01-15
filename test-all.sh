#!/bin/bash
# Run tests for all packages in the workspace

for pkg in mg mg-core mg-cli; do
  echo -n "$pkg: "
  output=$(cd "$(dirname "$0")/$pkg" && uv run pytest -q --tb=no "$@" 2>&1)
  echo "$output" | grep -E "^[0-9]+ passed|^FAILED|^ERROR|failed|error" | tail -1
done

# Type checking
type_errors=""
for pkg in mg mg-core mg-cli; do
  if ! (cd "$(dirname "$0")/$pkg" && uv run ty check 2>&1) > /dev/null; then
    type_errors="$type_errors $pkg"
  fi
done

if [ -n "$type_errors" ]; then
  echo -e "\033[31mType errors in:$type_errors (run ./type-all.sh for details)\033[0m"
fi
