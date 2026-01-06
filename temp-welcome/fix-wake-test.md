# Task Assignment

Load the following documents into context:
- ./src/mg_project/__assets__/roles/generalist.md (your role)
- ./worktrees/main/mg-core/tests/test_wake.py (the failing test)
- ./worktrees/main/mg-core/src/mg_core/commands/wake.py (the implementation)

---

## Task

**Diagnose and fix failing test in mg-core**

The test at `mg-core/tests/test_wake.py` is failing. Diagnose why and fix it.

If the issue is in test code, fix the test.
If the issue is in system code (mg or mg-core), fix the implementation.

**Location:** `worktrees/main/mg-core/`

---

## Success Criteria

- Test passes
- Fix is correct (not just making the test pass incorrectly)

---

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/tests/test_wake.py -v
```

---

## Process

1. Run the test, observe the failure
2. Read the test to understand what it expects
3. Read the implementation to understand what it does
4. Diagnose the mismatch
5. Fix and verify
