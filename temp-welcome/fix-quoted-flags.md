# Task Assignment

Load the following documents into context:
- ./src/mg_project/__assets__/roles/generalist.md (your role)
- ./worktrees/main/mg/src/mg/router.py (routing logic)
- ./worktrees/main/mg/src/mg/args.py (argument parsing)

---

## Task

**Fix mg routing to handle quoted flag arguments**

Currently, flag values with quotes aren't being parsed correctly. For example:

```bash
mg users new --name "Casey Smith"
```

The quoted string isn't being handled as a single value.

**Location:** `worktrees/main/mg/`

---

## Success Criteria

- Quoted flag values are parsed as a single argument
- `--name "Casey Smith"` results in name = "Casey Smith"
- Existing tests still pass
- Add tests for quoted values

---

## Verification

```bash
cd worktrees/main && uv run pytest mg/ -v
```

---

## Process

1. Write a failing test for quoted flag values
2. Find where argument parsing happens
3. Fix the parsing logic
4. Verify all tests pass
