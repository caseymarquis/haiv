# After Action Report: Param File Routing

**Task:** Fix failing `mg wake` test by adding param file support to router
**Date:** 2026-01-04

---

## Summary

The `mg wake wren` command failed to route because the router only supported param directories (`_mind_/`) but not param files (`_mind_.py`). Added param file support to the routing layer, along with proper ambiguity detection for `_rest_.py` coexisting with params.

---

## Deliverables

| Item | Location |
|------|----------|
| Implementation | `mg/src/mg/routing.py` |
| Tests | `mg/tests/test_routing.py` |
| Commit | `70c4e41` on `worktrees/main` |

---

## Diagnosis

The `wake/_mind_.py` pattern wasn't matching `mg wake wren` because:
1. Router checked for literal file (`wren.py`) - not found
2. Router checked for literal dir (`wren/`) - not found
3. Router checked for param dirs (`_mind_/`) - exists but expects subcommand
4. Router never checked for param files (`_mind_.py`)

---

## Solution

### 1. Param File Parsing
Added `_parse_param_file()` to handle `_name_.py` and `_target_as_mind_.py` patterns, mirroring the existing `_parse_param_dir()` logic.

### 2. Routing Logic
Modified `_find_matches()` to try param files when:
- Key matches `_*_.py` pattern
- No more route parts remain (leaf position)
- Not a dunder or `_rest_.py`

### 3. Ambiguity Detection
Added validation: `_rest_.py` cannot coexist with param files/dirs at same level. This prevents confusing route behavior where both could match.

---

## Precedence Rules (Unchanged)

1. Literal file/dir (highest)
2. Param file (new - single arg capture)
3. Param directory (descends for subcommands)
4. `_rest_.py` (captures remaining args)

Param file vs param dir with same name: file wins for single arg, dir wins when subcommand follows.

---

## Tests Added

| Test Class | Coverage |
|------------|----------|
| `TestParamFileCapture` | 12 tests - basic, explicit resolver, precedence, nesting |
| `TestRestFileAsLeaf` | 11 tests - rest/param ambiguity, literal resolution |

Total: 88 routing tests passing (was 61).

---

## Edge Cases Covered

- `_name_.py` vs `_name_/action.py` - file wins for 1 arg, dir wins for 2+
- `_rest_.py` + `_mind_.py` at same level - raises `AmbiguousRouteError`
- `_rest_.py` + `status.py` at same level - literal wins (allowed)
- `__init__.py` not treated as param file
- `_rest_/` as directory - not supported (only `_rest_.py` works)

---

## Open Items

None - all tests passing including original `mg-core/tests/test_wake.py`.
