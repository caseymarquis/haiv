# 006 — The Handler Pattern

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

Needed to find existing handlers to see the subscriber side. Searched the worktree first — nothing. Then checked the project level on haiv-hq and found one.

## What I Read

`src/haiv_project/haiv_hook_handlers/sync_packages.py`

## What I Found

### The only handler in the codebase

```python
@haiv_hook(AFTER_WORKTREE_CREATED, description="Syncing packages")
def sync_packages(req: WorktreeCreated, ctx: cmd.Ctx) -> None:
    subprocess.run(["uv", "sync", "--all-packages", "--quiet"], cwd=req.worktree_path, check=True)
```

Lives at the **project level** (`haiv_project/haiv_hook_handlers/`), not in core. This makes sense — `uv sync` is a project-specific concern. The hook point is defined in core (`AFTER_WORKTREE_CREATED`), but the response is project-specific.

### Handler conventions I can see

- File in `haiv_hook_handlers/` directory (not underscore-prefixed)
- Imports `@haiv_hook` from `haiv.haiv_hooks`
- Imports the hook point constant and request type from `haiv_core.haiv_hook_points`
- Decorated with `@haiv_hook(POINT, description="...")` — description is printed during emit
- Signature: `(req: RequestType, ctx: cmd.Ctx) -> ResponseType`
- Catches its own exceptions and prints warnings rather than crashing the command

### Key insight: handlers live at any package level

The hook point is in core, the handler is in project. A user-level handler could also subscribe to the same point. The discovery order (core → project → user) means project handlers run before user handlers.

### No handlers exist in the worktree

The worktree has no `haiv_hook_handlers/` directory at all. This is expected — the handler lives at the project level on haiv-hq, and the worktree is a code workspace.

## Where I'm Going Next

I've seen the full pattern end-to-end. Let me check the CLI integration briefly (how `enable_haiv_hooks` triggers discovery), then I can write up the complete picture.
