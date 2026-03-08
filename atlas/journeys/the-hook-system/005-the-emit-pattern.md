# 005 — The Emit Pattern in Practice

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

Needed to see how a command actually emits a hook — the concrete pattern, not just the API.

## What I Read

`haiv-core/src/haiv_core/commands/minds/stage.py`

## What I Found

### The three things a command does to use hooks

1. **`define()` declares `enable_haiv_hooks=True`** — this triggers the CLI to discover and register handlers at startup before the command runs.

2. **Imports the hook point and request type** from `haiv_hook_points.py`:
   ```python
   from haiv_core.haiv_hook_points import AFTER_WORKTREE_CREATED, WorktreeCreated
   ```

3. **Calls `.emit()` at the right moment** — after creating the worktree, before scaffolding the mind:
   ```python
   AFTER_WORKTREE_CREATED.emit(
       WorktreeCreated(
           worktree_path=worktree_path,
           branch=name,
           base_branch=base_branch,
           mind_name=name,
       ),
       ctx,
   )
   ```

### Placement matters

The hook fires between worktree creation (line 141-144) and mind scaffolding (line 159). This means handlers can do things like `uv sync` in the new worktree before the mind's files are set up. The ordering is intentional.

### What this means for `hv pop`

To add a hook to `pop.py`, the pattern is:
1. Add `enable_haiv_hooks=True` to its `define()`
2. Define a new hook point + request dataclass in `haiv_hook_points.py`
3. Call `.emit()` at the right place in `_do_merge()` or wherever makes sense

## Where I'm Going Next

Need to find existing handlers in `haiv_hook_handlers/` directories to see the subscriber side of the pattern. Also need to confirm how the CLI wires up the registry — I saw `enable_haiv_hooks` referenced in `haiv-cli/__init__.py`.
