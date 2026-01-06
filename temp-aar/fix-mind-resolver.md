# After Action Report: Fix ctx.paths Being None in Mind Resolver

**Date:** 2026-01-05
**Task:** Fix `mg become wren` failing with `AttributeError: 'NoneType' object has no attribute 'minds'`

---

## Summary

Fixed a bug where `ctx.paths` was always `None` in resolvers, causing `mg become wren` to fail.

## Root Cause

In `mg-cli/src/mg_cli/__init__.py:275`, the `make_resolver()` call was hardcoded to pass `paths=None`:

```python
resolve = make_resolver(pkg_roots, paths=None, has_user=mg_username is not None)
```

The `paths` object was correctly created on lines 264-269 inside an `if mg_root is not None` block, but this variable was scoped inside the conditional and never passed to `make_resolver`.

## Fix

Changed line 275 to pass the actual `paths` object:

```python
paths = None  # Initialize before conditional
if mg_root is not None:
    paths = Paths(...)
    # ... pkg_roots setup ...

resolve = make_resolver(pkg_roots, paths=paths, has_user=mg_username is not None)
```

**File:** `worktrees/main/mg-cli/src/mg_cli/__init__.py`

## Verification

1. `mg become wren` - runs without error
2. `uv run pytest mg-core/ -v` - 157 tests pass

## Lessons Learned

- When building context objects in conditionals, ensure they're passed to functions that need them
- The variable name `paths` was reused but the later reference was to a different scope
