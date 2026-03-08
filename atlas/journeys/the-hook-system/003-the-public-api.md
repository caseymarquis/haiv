# 003 — The Public API

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

The infrastructure layer told me command authors use `haiv.haiv_hooks`. I needed to see the types and decorators they actually interact with.

## What I Read

`haiv-lib/src/haiv/haiv_hooks.py`

## What I Found

### Three pieces to the public API

1. **`HaivHookPoint[TReq, TRes]`** — A typed extension point. Dataclass with a `guid` string and an `emit(request, ctx)` method. Generic over request and response types. `TRes=None` for fire-and-forget hooks.

2. **`@haiv_hook(point, description="...")`** — Decorator that stamps `_haiv_hook_guid` and `_haiv_hook_description` on a function. Doesn't register immediately — registration happens at CLI startup via `configure_haiv_hooks()`.

3. **`HaivHookHandler`** — Protocol for decorated functions. Has `_haiv_hook_guid`, `_haiv_hook_description`, `_haiv_hook_source` (source set later during configure).

### The module docstring is a complete usage guide

Three usage patterns laid out clearly:

- **Defining** a hook point: create a request dataclass + a `HaivHookPoint` constant in a `haiv_hook_points.py` module
- **Emitting**: import the constant, call `.emit(request, ctx)` from a command with `enable_haiv_hooks=True`
- **Handling**: decorate a function with `@haiv_hook(POINT, description="...")`, place it in `haiv_hook_handlers/`

### Error design

`emit()` resolves the registry from `ctx._haiv_hook_registry`. If hooks aren't enabled (registry is None), it raises with a clear message telling you to add `enable_haiv_hooks=True`. Exceptions from handlers propagate by design — callers choose whether to guard.

## Where I'm Going Next

`haiv-core/haiv_hook_points.py` — the existing hook point definitions. I already read this file but need to write the entry. Then I need to see how `stage.py` emits the hook and find existing handlers.
