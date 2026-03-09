# 007 — The CLI Wiring

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

Needed to confirm how `enable_haiv_hooks=True` triggers discovery at the CLI level.

## What I Read

`haiv-cli/src/haiv_cli/__init__.py` (just the relevant section via grep, lines 296-314)

## What I Found

After routing and loading, the CLI:

1. Calls `command.define()` to get the definition
2. Checks `definition.enable_haiv_hooks`
3. If true: `configure_haiv_hooks(pkg_roots)` → builds a populated `HaivHookRegistry`
4. Passes the registry into `build_ctx()` as `haiv_hook_registry=`
5. The registry lands on `ctx._haiv_hook_registry`
6. When the command calls `HOOK_POINT.emit(request, ctx)`, it reads the registry from ctx

If `enable_haiv_hooks` is false, the registry is None. If the command tries to emit anyway, `HaivHookPoint.emit()` raises with a clear error message.

### The lazy discovery design

Hooks are only discovered and loaded for commands that opt in. A command that doesn't need hooks pays no discovery cost. This is why it's a flag on `Def` rather than always-on.

## The Complete Picture

I now have the full hook system mapped:

```
Define hook point          haiv_core/haiv_hook_points.py
  ↓                          HaivHookPoint + request dataclass
Command opts in            define() → enable_haiv_hooks=True
  ↓
CLI discovers handlers     haiv_hook_handlers/ in core → project → user
  ↓
CLI builds registry        configure_haiv_hooks(pkg_roots) → HaivHookRegistry
  ↓
Registry goes on ctx       ctx._haiv_hook_registry
  ↓
Command emits              HOOK_POINT.emit(RequestData(...), ctx)
  ↓
Registry calls handlers    In registration order, prints description, returns results
```

This journey is complete. Time to update the map and quest board.
