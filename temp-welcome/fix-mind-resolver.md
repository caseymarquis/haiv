# Task Assignment

Load the following documents into context:
- ./src/mg_project/__assets__/roles/generalist.md (your role)
- ./worktrees/main/mg-core/src/mg_core/resolvers/mind.py (the failing resolver)
- ./worktrees/main/mg/src/mg/args.py (context building)

---

## Task

**Fix ctx.paths being None in mind resolver**

Running `mg become wren` fails with:
```
AttributeError: 'NoneType' object has no attribute 'minds'
```

The error occurs at `mg-core/src/mg_core/resolvers/mind.py:27` when trying to access `ctx.paths.minds`, but `ctx.paths` is `None`.

**Location:** `worktrees/main/mg-core/` and possibly `worktrees/main/mg/`

---

## Success Criteria

- `mg become wren` runs without the AttributeError
- Mind resolver correctly accesses the minds path
- Existing tests still pass

---

## Verification

```bash
mg become wren
cd worktrees/main && uv run pytest mg-core/ -v
```

---

## Process

1. Understand how ctx.paths should be populated (check args.py)
2. Find why it's None when the resolver runs
3. Fix the initialization order or add proper error handling
4. Verify the fix works
