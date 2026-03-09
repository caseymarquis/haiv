# 004 — Existing Hook Points

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

Needed to see the existing hook point definitions — the concrete examples of the pattern.

## What I Read

`haiv-core/src/haiv_core/haiv_hook_points.py`

## What I Found

### Convention documented at the top

Each package that emits hooks should have a `haiv_hook_points.py` at its root — the single source of truth for request dataclasses, response types, and HaivHookPoint constants. Both emitting commands and remote handlers import from here.

### Naming conventions

- Constants: `AFTER_<EVENT>` or `BEFORE_<EVENT>`, uppercase
- GUIDs: `{package}:{command-path}:{timing}-{event}`, e.g. `haiv-core:minds:stage:after-worktree-created`
- Request dataclasses: named after the event, e.g. `WorktreeCreated`

### The one existing hook point

```python
@dataclass
class WorktreeCreated:
    worktree_path: Path
    branch: str
    base_branch: str
    mind_name: str

AFTER_WORKTREE_CREATED = HaivHookPoint[WorktreeCreated, None](
    guid="haiv-core:minds:stage:after-worktree-created",
)
```

Fire-and-forget (`None` response type). Emitted after `hv minds stage` creates a worktree.

### Interesting: the docstring already has an example for `hv pop`

The docstring includes a hypothetical `AFTER_BRANCH_MERGED` hook point with guid `haiv-core:pop:after-branch-merged`. Someone was already thinking about this.

## Where I'm Going Next

Two threads to follow:
1. `stage.py` — see how the existing hook is emitted
2. Find existing handlers in `haiv_hook_handlers/` directories
