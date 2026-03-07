# Task Assignment

**Project Manager: `hv minds suggest_role` implementation**

You designed this feature (see your AAR at `temp-aar/suggest-role-design.md`). Now oversee its implementation by delegating work packages sequentially to other minds.

**Worktree:** `worktrees/suggest-role/` (paths relative to repo root)

---

## Context

Your immediate-plan.md contains the full work breakdown with 6 work packages (WP1-WP6). You identified dependencies and execution order during design.

**Can start immediately:** WP1 (test module refactor), WP4 (roles helper)
**Needs design first:** WP2 (caching infrastructure)

---

## Requirements

1. Delegate work packages one at a time
2. Review each AAR before proceeding to next
3. Verify work compiles/tests pass
4. Update your immediate-plan.md as work completes
5. Write final AAR when project completes

---

## Success Criteria

- All 6 work packages completed
- `hv minds suggest_role --name <mind>` works end-to-end
- Tests pass in suggest-role worktree
- Branch ready for review/merge
