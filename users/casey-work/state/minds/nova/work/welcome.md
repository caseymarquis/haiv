# Task Assignment

**Fix: Windows test compatibility**

The haiv test suite has failures when run on Windows. Your job is to investigate and fix them so tests pass on both Linux and Windows.

**Location:** `worktrees/nova/`

---

## Known Failures

From nova's previous AAR (`users/casey-work/state/minds/rove/work/aars/feat-chart-use-project-local-example-journey-ae7e.md`):

- **`test_become` and `test_mine`** (2 failures) — Windows path separator issue. Tests assert forward-slash paths but Windows produces backslashes.
- **`test_minds_stage` and `test_pop`** (88 errors) — Cause not investigated. Start here to understand the scope.

## Requirements

- Tests must pass on Windows (the current platform)
- Tests must continue to pass on Linux (don't break the other direction)
- Fixes should be in the test infrastructure or production code as appropriate — not just test workarounds

---

## Success Criteria

- `uv run pytest` passes from within each package directory (haiv-core, haiv-lib, haiv-cli, haiv)
- No platform-specific test skips unless truly unavoidable

---

## Verification

```bash
cd worktrees/nova/haiv-core && uv run pytest
cd worktrees/nova/haiv-lib && uv run pytest
cd worktrees/nova/haiv-cli && uv run pytest
cd worktrees/nova/haiv && uv run pytest
```

---

## Process

1. Run the test suite, catalog all failures
2. Identify root causes (path separators, OS assumptions, etc.)
3. Fix in order of impact (88-error block first if it's a single root cause)
4. Verify on Windows, reason about Linux compatibility

---

## Before You Begin

1. Read the full assignment above.
2. Run `hv chart` and check the maps for anything relevant to your task.
3. **Decision point:** Does the Atlas have what you need to understand the codebase for this task?
   - **Yes** → Continue to step 4.
   - **No** → Propose an exploration to your human collaborator. What territory do you need to chart? This becomes a journey before you write code.
4. Discuss your approach with your human collaborator.

Use `TaskCreate` to track these steps — there may be significant work between them. The task description is a starting point — not a spec. Work collaboratively with your human. Do not use planning tools unless they explicitly request it.

> **IMPORTANT:** When you need to explore the codebase, follow the `hv chart` process. Do NOT read through code files without it. Exploration that follows the charting process builds the Atlas for future minds. Exploration that doesn't is wasted.
>
> Before starting your exploration, read the most recent journey in `atlas/journeys/` to see what the process looks like in practice. Then state the charting rules back to your human before you begin. If you can't articulate the rules, you haven't understood them yet.
