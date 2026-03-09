# 002 — The Infrastructure Layer

**Explorer:** Ember
**Date:** 2026-03-08

---

## Why I Came Here

`haiv_hooks.py` exists in two places — `_infrastructure/haiv_hooks.py` (discovery, loading, registry) and `haiv/haiv_hooks.py` (public API). The infrastructure file's docstring says command authors don't use it directly. I started here to understand the plumbing.

## What I Read

`haiv-lib/src/haiv/_infrastructure/haiv_hooks.py`

## What I Found

### HaivHookRegistry

Central store of handlers, keyed by hook point GUID. Populated at CLI startup when a command declares `enable_haiv_hooks=True`. Two key methods:

- `register(guid, handler)` — called during startup, not by user code
- `emit(guid, request, ctx)` — calls all handlers in registration order (core → project → user). Prints each handler's description and source file before calling it. Returns list of results.

### Discovery pipeline

Four functions that form a pipeline:

1. `discover_haiv_hooks(pkg_root)` — finds `.py` files in `pkg_root/haiv_hook_handlers/`, ignoring `_`-prefixed files
2. `load_haiv_hook_module(path)` — dynamic import via `importlib.util`, broken modules are skipped with a warning
3. `collect_haiv_handlers(module)` — scans module for functions with `_haiv_hook_guid` attribute (set by `@haiv_hook` decorator)
4. `configure_haiv_hooks(pkg_roots)` — orchestrates the above, builds a populated registry

### Security

Only first-party packages (`haiv_core`, `haiv_project`, `haiv_user`) can provide hooks. Untrusted packages raise `RuntimeError`.

### Key detail

The docstring says command authors use `haiv.haiv_hooks.HaivHookPoint` and `@haiv.haiv_hooks.haiv_hook` — the public API is in a separate file.

## Where I'm Going Next

The public API: `haiv/haiv_hooks.py`.
