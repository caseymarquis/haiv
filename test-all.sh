#!/bin/bash
# Run tests for all packages in the workspace (parallel across and within packages)

dir="$(dirname "$0")"
pids=()
tmpfiles=()

for pkg in haiv haiv-core haiv-cli; do
  tmp=$(mktemp)
  tmpfiles+=("$tmp")
  (cd "$dir/$pkg" && uv run pytest -n auto --dist loadgroup -q --tb=no "$@" 2>&1 | tail -1 | sed "s/^/$pkg: /") > "$tmp" &
  pids+=($!)
done

for i in "${!pids[@]}"; do
  wait "${pids[$i]}"
  cat "${tmpfiles[$i]}"
  rm -f "${tmpfiles[$i]}"
done

# Type checking (parallel)
type_pids=()
type_tmps=()

for pkg in haiv haiv-core haiv-cli; do
  tmp=$(mktemp)
  type_tmps+=("$tmp")
  (cd "$dir/$pkg" && uv run ty check 2>&1 > /dev/null && echo "ok" || echo "fail") > "$tmp" &
  type_pids+=($!)
done

type_errors=""
for i in "${!type_pids[@]}"; do
  wait "${type_pids[$i]}"
  result=$(cat "${type_tmps[$i]}")
  rm -f "${type_tmps[$i]}"
  if [ "$result" = "fail" ]; then
    pkgs=(haiv haiv-core haiv-cli)
    type_errors="$type_errors ${pkgs[$i]}"
  fi
done

if [ -n "$type_errors" ]; then
  echo -e "\033[31mType errors in:$type_errors (run ./type-all.sh for details)\033[0m"
fi
